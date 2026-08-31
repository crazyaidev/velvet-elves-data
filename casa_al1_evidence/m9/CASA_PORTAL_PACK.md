# CASA AL1 — portal pack (comments and image descriptions)

**Filename (fixed):** `casa_al1_evidence/m9/CASA_PORTAL_PACK.md` — do not rename. Append new rows here; update the scope line only.  
**Updated:** 31 Aug 2026  
**Rows in this file:** 1.1.1, 1.1.2, 1.1.3, 1.2.1, 1.3.1, 1.3.2, 1.3.3, 1.3.4, 2.1.1, 2.2.1, 2.2.2, 2.2.3, 2.3.1, 2.3.2, 2.3.3, 2.3.4, 2.4.1, 3.1.1, 3.1.2, 3.1.3, 3.1.4, 3.1.5, 3.1.6, 3.2.1, 3.2.2, 3.3.1, 4.1.1, 4.1.2, 4.1.3, 4.1.4, 5.1.1, 5.1.2, 5.1.3, 5.1.4, 5.1.5, 5.1.6, 5.1.7, 5.1.8, 5.1.9, 5.1.10, 5.2.1, 6.1.1, 6.2.1, 6.3.1, 6.4.1, 6.5.1, 6.6.1, 6.7.1  
**Portal:** https://casa.tacsecurity.com/ — per-row **Upload Evidences** (PNG/JPG/JPEG, max 10). Do not upload this markdown.  
**Images:** `casa_al1_evidence/m9/tac_images/<check-id>/` — one folder per row. MFA shots for later row 3.3.1 are in `tac_images/3.3.1/` (do not attach those on 1.1.x / 1.2.1).  
**Operating guide:** `CASA/TAC_ESOF_PORTAL_GUIDE.md` §7  
**Missing screenshots (checklist):** `CASA/MISSING_SCREENSHOTS_CHECKLIST.md`  
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
| 12 | 2.2.3 | Stateless authentication tokens expire within 24 hours | 6 | `CASA_2_2_3_stateless_expiry.md` |
| 13 | 2.3.1 | Cookie-based session tokens shall have the Secure attribute | 5 | `CASA_2_3_1_cookie_secure.md` |
| 14 | 2.3.2 | Cookie-based session tokens shall have the HttpOnly attribute | 5 | `CASA_2_3_2_cookie_httponly.md` |
| 15 | 2.3.3 | Session tokens rather than static API secrets and keys | 4 | `CASA_2_3_3_session_not_static_key.md` |
| 16 | 2.3.4 | Stateless session tokens shall use digital signatures | 5 | `CASA_2_3_4_signed_jwt.md` |
| 17 | 2.4.1 | Full login session or re-auth before sensitive account changes | 5 | `CASA_2_4_1_sensitive_changes.md` |
| 18 | 3.1.1 | Least privilege access control on a trusted service layer | 5 | `CASA_3_1_1_least_privilege.md` |
| 19 | 3.1.2 | Users cannot manipulate access-control attributes | 5 | `CASA_3_1_2_policy_attrs.md` |
| 20 | 3.1.3 | Access controls fail securely | 5 | `CASA_3_1_3_fail_secure.md` |
| 21 | 3.1.4 | Sensitive resources protected against IDOR | 5 | `CASA_3_1_4_idor.md` |
| 22 | 3.1.5 | Anti-CSRF / anti-automation | 6 | `CASA_3_1_5_csrf.md` |
| 23 | 3.1.6 | Directory browsing disabled | 6 | `CASA_3_1_6_directory.md` |
| 24 | 3.2.1 | OAuth authorization code + PKCE | 6 | `CASA_3_2_1_oauth_pkce.md` |
| 25 | 3.2.2 | OAuth redirect_uri and state | 6 | `CASA_3_2_2_redirect_state.md` |
| 26 | 3.3.1 | Admin MFA on platform console | 10 | `CASA_3_3_1_admin_mfa.md` |
| 27 | 4.1.1 | TLS 1.2+ | 9 | `CASA_4_1_1_tls.md` |
| 28 | 4.1.2 | Trusted TLS certificates | 10 | `CASA_4_1_2_certs.md` |
| 29 | 4.1.3 | No weak crypto on secrets | 6 | `CASA_4_1_3_crypto.md` |
| 30 | 4.1.4 | Crypto fail securely | 6 | `CASA_4_1_4_fail_closed.md` |
| 31 | 5.1.1 | HTTP parameter pollution | 5 | `CASA_5_1_1_hpp.md` |
| 32 | 5.1.2 | Open redirect / allowlisted URLs | 6 | `CASA_5_1_2_redirect.md` |
| 33 | 5.1.3 | No eval / code injection | 5 | pack 5.1.3 |
| 34 | 5.1.4 | Template injection | 5 | pack 5.1.4 |
| 35 | 5.1.5 | SSRF | 6 | pack 5.1.5 |
| 36 | 5.1.6 | XML / XPath | 5 | pack 5.1.6 |
| 37 | 5.1.7 | XSS | 6 | pack 5.1.7 |
| 38 | 5.1.8 | SQLi | 6 | pack 5.1.8 |
| 39 | 5.1.9 | OS command injection | 5 | pack 5.1.9 |
| 40 | 5.1.10 | LFI / RFI | 6 | pack 5.1.10 |
| 41 | 5.2.1 | Malicious uploads | 6 | pack 5.2.1 |
| 42 | 6.1.1 | Dependency scan | 7 | pack 6.1.1 |
| 43 | 6.2.1 | Debug off in production | 6 | pack 6.2.1 |
| 44 | 6.3.1 | Origin not authz | 5 | pack 6.3.1 |
| 45 | 6.4.1 | Subdomain takeover | 5 | pack 6.4.1 |
| 46 | 6.5.1 | No credential logs | 4 | pack 6.5.1 — log samples missing |
| 47 | 6.6.1 | Logout clears storage | 5 | pack 6.6.1 |
| 48 | 6.7.1 | Server secrets | 3 | pack 6.7.1 — no AWS console |

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
- Production GoTrue **Authentication → Sessions** (31 Aug 2026): **Access token expiry time = 3600 seconds (1 hour)**.
- Staging GoTrue **Authentication → Sessions** (VelvetElves Stage, 31 Aug 2026, owner-captured): **Access token expiry time = 3600 seconds (1 hour)**. The orange **PRODUCTION** badge is that project's primary-branch label, not `app.velvetelves.com`.
- Staging live `POST /users/login` then decode `iat` / `exp` after that change (31 Aug 2026): **3600 seconds (1.00 hour)**, ES256. Token not shown. Earlier the same day (and on 28 Aug) staging still issued **28800 s**.
- Both environments are under ADA's **24-hour** cap.
- `decode_access_token` verifies the JWT; expired tokens raise `JWTError` → 401.
- SPA reads `exp` (`getTokenExpirationMs`) and silent-refreshes ~60 s before expiry.

**Do not claim:** that staging still issues 8-hour JWTs (that was true until the owner set 3600 s on 31 Aug); that the refresh token expires within 24 hours; that **Inactivity timeout** or **Time-box user sessions** (both 0 = never on these PNGs) are the 2.2.3 control — those are not the access JWT `exp`; that the Stage project's **PRODUCTION** badge is the production app host; HttpOnly cookies; invite/reset/mailbox tokens as the session JWT; pasting JWTs.

**Helpers:** `casa_auth_qa/render_casa_223_pages.py`, `casa_223_exp.py` (`QA_PASSWORD`). Owner Sessions shots are `CASA_2_2_3_supabase_jwt.png` (prod) and `CASA_2_2_3_supabase_jwt_stage.png` (VelvetElves Stage) — do **not** recapture supabase.com.

### Images

| File | Description |
| --- | --- |
| [`tac_images/2.2.3/CASA_2_2_3_page1.png`](tac_images/2.2.3/CASA_2_2_3_page1.png) | Written evidence page 1 of 2. Access JWT vs refresh; 1-hour lifetime on staging and production; API and SPA exp handling. |
| [`tac_images/2.2.3/CASA_2_2_3_page2.png`](tac_images/2.2.3/CASA_2_2_3_page2.png) | Written evidence page 2 of 2. AL1 mapping. Measured from live staging login after the Sessions change. |
| [`tac_images/2.2.3/CASA_2_2_3_code.png`](tac_images/2.2.3/CASA_2_2_3_code.png) | `decode_access_token` verifies `exp`; SPA `getTokenExpirationMs` and silent refresh 60 s before expiry. |
| [`tac_images/2.2.3/CASA_2_2_3_exp.png`](tac_images/2.2.3/CASA_2_2_3_exp.png) | Staging API: login 200, JWT `exp − iat` = 3600 s (1.00 hour), under 24 hours. Token not shown. |
| [`tac_images/2.2.3/CASA_2_2_3_supabase_jwt.png`](tac_images/2.2.3/CASA_2_2_3_supabase_jwt.png) | Production Supabase Authentication → Sessions. Access token expiry **3600 s**. No keys. Inactivity/time-box 0 is not this row. |
| [`tac_images/2.2.3/CASA_2_2_3_supabase_jwt_stage.png`](tac_images/2.2.3/CASA_2_2_3_supabase_jwt_stage.png) | VelvetElves Stage Authentication → Sessions. Access token expiry **3600 s**. No keys. Inactivity/time-box 0 is not this row. |

### Portal comment

```
The user session access token is a signed JWT. Production and staging GoTrue Sessions both set access token expiry to 3600 seconds (1 hour). Staging login on 31 Aug 2026 issued tokens with exp minus iat of 3600 seconds. Both environments are under ADA's 24-hour cap. The API rejects expired JWTs. The app reads exp and refreshes about a minute before expiry. The refresh token is a separate, revocable session token (see 2.2.1), not the stateless token this row covers.
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

## 3.1.1 — Least privilege access control on a trusted service layer

**ADA:** enforce least privilege on a **trusted service layer**. AL1 is documentation of authn/authz, roles, and that users only reach authorized functions. Verification: rules run on that layer. ADA says **3.1.1–3.1.3 share one written description** (`CASA_3_1_1_least_privilege.md`).

**Claimed controls**

- Enforcement is FastAPI: `get_current_user`, `require_role`, `require_tenant_access`, `require_transaction_access`. SPA `RoleRoute` is UX.
- Roles: Agent, TransactionCoordinator, TeamLead, Attorney, Admin, Client, ForSaleByOwner, Vendor. Admin satisfies all role checks; Agent satisfies Agent only. `is_platform_admin` is a separate flag.
- Tenant Admin is not cross-tenant. Platform `/api/v1/platform/*` needs the flag plus AAL2.
- Staging 31 Aug 2026: unsigned `GET /users/` and `GET /platform/users` → **401**.
- Tests: `test_rbac.py` (Client cannot create transactions; Agent cannot GET another user) plus M9f isolation tests.

**Do not claim:** RLS as the primary control (service-role can bypass it); a live Agent-vs-Admin probe on staging this session; MFA for all users; HttpOnly cookies.

**Helpers:** `casa_auth_qa/render_casa_311_pages.py`, `casa_311_deny.py`. Do **not** attach `/login`.

### Images

| File | Description |
| --- | --- |
| [`tac_images/3.1.1/CASA_3_1_1_page1.png`](tac_images/3.1.1/CASA_3_1_1_page1.png) | Written evidence page 1 of 2. API as trusted layer; roles; least-privilege examples. |
| [`tac_images/3.1.1/CASA_3_1_1_page2.png`](tac_images/3.1.1/CASA_3_1_1_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/3.1.1/CASA_3_1_1_code.png`](tac_images/3.1.1/CASA_3_1_1_code.png) | ROLE_HIERARCHY, require_role, require_tenant_access, platform admin. |
| [`tac_images/3.1.1/CASA_3_1_1_tests.png`](tac_images/3.1.1/CASA_3_1_1_tests.png) | Named RBAC and isolation tests. Not a pytest product screenshot. |
| [`tac_images/3.1.1/CASA_3_1_1_deny.png`](tac_images/3.1.1/CASA_3_1_1_deny.png) | Staging unsigned GET /users/ and GET /platform/users both 401. |

### Portal comment

```
Access control is enforced on the API (FastAPI), not only in the browser. Roles are Agent, TransactionCoordinator, TeamLead, Attorney, Admin, Client, ForSaleByOwner, and Vendor. Endpoints use get_current_user plus require_role, require_tenant_access, and require_transaction_access. Tenant Admin is not cross-tenant. Platform /api/v1/platform/* requires is_platform_admin and AAL2. Staging unsigned GET /users/ and GET /platform/users return 401. Postgres RLS is defense in depth; the API is the trusted layer.
```

---

## 3.1.2 — Users cannot manipulate access-control attributes

**ADA:** attributes used by access controls must not be manipulated by the end user unless specifically authorized. AL1 shares the 3.1.1–3.1.3 written description. Verification: those attributes are not client-set.

**Claimed controls**

- `get_current_user` loads `role`, `tenant_id`, `is_platform_admin`, `is_active` from the profile after JWT `sub`.
- Register ignores client `tenant_id` and mints a new tenant. OAuth ignores `user_metadata.tenant_id` (and OAuth role).
- `UserUpdateRequest` has no `role` / `tenant_id` / `is_platform_admin` / `is_active`. Extra `is_active` is ignored.
- After signup, role changes are `PUT /users/{id}/role` in the same tenant. No self-service `is_platform_admin`.
- Staging 31 Aug 2026: unsigned `PATCH /users/me` with those extras → **401**.

**Do not claim:** register ignores role entirely (founder may pick a self-signup role on the **new** tenant); `X-Workspace-Id` is ignored (membership-checked); a live authenticated extras probe this session (`QA_PASSWORD` was not set).

**Helpers:** `casa_auth_qa/render_casa_312_pages.py`, `casa_312_ignore.py`. Do **not** attach `/login`. Do **not** register a staging user to prove tenant_id ignore.

### Images

| File | Description |
| --- | --- |
| [`tac_images/3.1.2/CASA_3_1_2_page1.png`](tac_images/3.1.2/CASA_3_1_2_page1.png) | Written evidence page 1 of 2. Server profile; tenant_id ignored at signup; PATCH /me has no policy fields. |
| [`tac_images/3.1.2/CASA_3_1_2_page2.png`](tac_images/3.1.2/CASA_3_1_2_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/3.1.2/CASA_3_1_2_code.png`](tac_images/3.1.2/CASA_3_1_2_code.png) | Register/OAuth ignore tenant_id; UserUpdateRequest; get_current_user from DB. |
| [`tac_images/3.1.2/CASA_3_1_2_tests.png`](tac_images/3.1.2/CASA_3_1_2_tests.png) | Named tests for ignored tenant_id, OAuth, self-deactivate, onboarding role. |
| [`tac_images/3.1.2/CASA_3_1_2_ignore.png`](tac_images/3.1.2/CASA_3_1_2_ignore.png) | Staging unsigned PATCH /users/me with role, tenant_id, is_platform_admin, is_active → 401. |

### Portal comment

```
Role, tenant, platform-admin, and active flags used for access control come from the server profile after JWT verification, not from client JSON. Register ignores client tenant_id and mints a new tenant. OAuth ignores user_metadata tenant_id. PATCH /users/me has no role, tenant_id, is_platform_admin, or is_active fields; extra is_active is ignored. Role changes after signup go through PUT /users/{id}/role in the same tenant. Staging unsigned PATCH /users/me with those extra fields returns 401.
```

---

## 3.1.3 — Access controls fail securely

**ADA:** access controls shall fail securely, including when an exception occurs (ASVS 4.1.5). AL1 shares the 3.1.1–3.1.3 written description (`CASA_3_1_1_least_privilege.md`). Verification: missing or bad credentials deny; authorization misses deny; exceptions do not return the resource.

**Claimed controls**

- Missing `Authorization` → FastAPI OAuth2 bearer **401**. Invalid / expired / garbage JWT (`JWTError`) or missing profile → **401**. Inactive user and suspended tenant → **403**.
- `require_role` / `require_tenant_access` raise **403**; they do not return 200 with data. Some cross-owner reads return **404** (still deny).
- Scheduler `POST /internal/schedules/tick` requires `X-VE-Cron-Secret` and **fails closed** if the secret is unset (`require_cron_secret`).
- Unhandled exceptions → generic **500** `"An internal server error occurred."` (`APP_DEBUG` must be false in production).
- Staging 31 Aug 2026: `GET /users/me` no auth and `Bearer not-a-jwt` → **401**; `POST /internal/schedules/tick` without the cron header → **403**. The tick was not run.

**Do not claim:** every deny is 403 (missing auth is 401); stack traces in API JSON; a live DB-exception probe; MFA for all users; HttpOnly cookies.

**Helpers:** `casa_auth_qa/render_casa_313_pages.py`, `casa_313_fail.py`. Do **not** attach `/login`. Do **not** call the tick with a valid secret.

### Images

| File | Description |
| --- | --- |
| [`tac_images/3.1.3/CASA_3_1_3_page1.png`](tac_images/3.1.3/CASA_3_1_3_page1.png) | Written evidence page 1 of 2. Missing/bad credentials 401; authz 403; exceptions do not grant access. |
| [`tac_images/3.1.3/CASA_3_1_3_page2.png`](tac_images/3.1.3/CASA_3_1_3_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/3.1.3/CASA_3_1_3_code.png`](tac_images/3.1.3/CASA_3_1_3_code.png) | JWTError → 401; cron secret fail-closed; generic 500. |
| [`tac_images/3.1.3/CASA_3_1_3_tests.png`](tac_images/3.1.3/CASA_3_1_3_tests.png) | Named tests for 401, role 403, cron fail-closed. |
| [`tac_images/3.1.3/CASA_3_1_3_fail.png`](tac_images/3.1.3/CASA_3_1_3_fail.png) | Staging: GET /users/me no auth and Bearer not-a-jwt → 401; POST tick without secret → 403. |

### Portal comment

```
Access control fails closed. Missing Authorization returns 401. An invalid JWT raises JWTError and returns 401; it does not load a user. Role, tenant, and assignment misses return 403 (some cross-owner reads return 404). The scheduler tick requires X-VE-Cron-Secret and fails closed if the secret is unset. Unhandled exceptions return a generic 500, not the resource. Staging: GET /users/me without Authorization and with Bearer not-a-jwt both 401; POST /internal/schedules/tick without the cron header returns 403.
```

---

## 3.1.4 — Sensitive resources protected against IDOR

**ADA:** protect sensitive resources against IDOR on create/read/update/delete (ASVS 4.2.1). AL1: list APIs that take a user-supplied URL or parameter ID, and describe how they are protected. Verification: a process is in place to mitigate IDOR.

**Claimed controls**

- Path IDs include `/users/{id}`, `/tenants/{id}`, `/transactions/{id}` (and nested deal routes), `/documents/{id}`, `/invoices/{id}`, `/payments/{id}`, `/tasks/{id}`, `/teams/{id}`, `/audit-logs/{type}/{id}`, and `/platform/.../{id}`. Lists are tenant-scoped.
- After JWT verification the API loads the row and calls `require_tenant_access` (**403** other tenant). Deals also use `require_transaction_access` (Agent must be creator or assigned). Tenant Admin is not cross-tenant.
- Cross-owner FSBO and unrelated documents often **404**. Audit entity reads filter `current_user.tenant_id`.
- Staging 31 Aug 2026: unsigned GET of a placeholder UUID on `/transactions`, `/users`, `/tenants`, `/documents`, `/invoices` → **401**. No other tenant was queried.

**Do not claim:** a live authenticated two-tenant IDOR replay this session; that ZAP ran WSTG-ATHZ-04; that every object route uses `require_tenant_access` (`GET /contacts/{id}` currently skips the tenant deny when `role == Admin`); RLS as the primary control.

**Helpers:** `casa_auth_qa/render_casa_314_pages.py`, `casa_314_deny.py`. Do **not** attach `/login`. Do **not** register a staging user. Do **not** query another tenant.

### Images

| File | Description |
| --- | --- |
| [`tac_images/3.1.4/CASA_3_1_4_page1.png`](tac_images/3.1.4/CASA_3_1_4_page1.png) | Written evidence page 1 of 2. ID-parameter API families; IDOR process; staging unsigned 401. |
| [`tac_images/3.1.4/CASA_3_1_4_page2.png`](tac_images/3.1.4/CASA_3_1_4_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/3.1.4/CASA_3_1_4_code.png`](tac_images/3.1.4/CASA_3_1_4_code.png) | require_transaction_access; GET /users/{id} tenant check; audit tenant filter. |
| [`tac_images/3.1.4/CASA_3_1_4_tests.png`](tac_images/3.1.4/CASA_3_1_4_tests.png) | Named isolation tests (403/404/empty). |
| [`tac_images/3.1.4/CASA_3_1_4_deny.png`](tac_images/3.1.4/CASA_3_1_4_deny.png) | Staging unsigned GET of placeholder UUIDs on five ID paths → 401. |

### Portal comment

```
User-supplied object IDs appear in paths such as /users/{id}, /tenants/{id}, /transactions/{id}, /documents/{id}, /invoices/{id}, /tasks/{id}, /teams/{id}, and /audit-logs/{type}/{id}. Knowing a UUID is not enough. After JWT verification the API loads the row and checks tenant (require_tenant_access) and, for deals, assignment (require_transaction_access). Lists are tenant-scoped. A tenant Admin cannot read or change another org's tenant or users (403). Cross-owner FSBO and unrelated document reads return 404. Staging unsigned GET of those ID paths with a placeholder UUID returns 401.
```

---

## 3.1.5 — Anti-CSRF for authenticated APIs; anti-automation for unauthenticated

**ADA:** strong anti-CSRF on authenticated functionality; anti-automation or anti-CSRF on unauthenticated functionality (ASVS 4.2.2). AL1 evidence is ADA DAST. Verification: the scan shall not identify Burp **2098944**. Official scans were ZAP (SPA 10202/20012 = FAIL).

**Claimed controls**

- Authenticated APIs use `Authorization: Bearer` from `localStorage`, not a cookie session. Login JSON JWTs; staging `Set-Cookie` none (2.3.1). A cross-site form cannot attach the Bearer header.
- CORS allowlists exact origins. A foreign `Origin` is not echoed as `Access-Control-Allow-Origin`.
- Unauthenticated: register **5 / 60 s / IP**; login **10 / 60 s / IP**.
- Official ZAP SPA `10f54abf`, API `a9d78f05`, auth `33afa2aa` did not list 10202 / 20012.
- Staging 31 Aug 2026: OPTIONS `/users/me` from `app.stage.velvetelves.com` → **200** + that origin; `evil.example` → **400** and no ACAO. Register 429 PNG copied from 1.1.1 (no new users minted).

**Do not claim:** a synchronizer CSRF cookie; HttpOnly cookies; that CORS methods/headers are locked (`*` — origins are the control); that Burp 2098944 ran; CAPTCHA.

**Helpers:** `casa_auth_qa/render_casa_315_pages.py`, `casa_315_cors.py`. Do **not** attach `/login`. Do **not** recapture ZAP UI. Do **not** register staging users for a fresh 429.

### Images

| File | Description |
| --- | --- |
| [`tac_images/3.1.5/CASA_3_1_5_page1.png`](tac_images/3.1.5/CASA_3_1_5_page1.png) | Written evidence page 1 of 2. Bearer not cookie; register limiter; ZAP. |
| [`tac_images/3.1.5/CASA_3_1_5_page2.png`](tac_images/3.1.5/CASA_3_1_5_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/3.1.5/CASA_3_1_5_code.png`](tac_images/3.1.5/CASA_3_1_5_code.png) | CORSMiddleware origins; Bearer header; register/login limiters. |
| [`tac_images/3.1.5/CASA_3_1_5_zap.png`](tac_images/3.1.5/CASA_3_1_5_zap.png) | Official ADA ZAP CSRF rule excerpt. Not a ZAP product screenshot. |
| [`tac_images/3.1.5/CASA_3_1_5_cors.png`](tac_images/3.1.5/CASA_3_1_5_cors.png) | Staging OPTIONS: SPA origin allowed; evil.example not echoed. |
| [`tac_images/3.1.5/CASA_3_1_5_register_429.png`](tac_images/3.1.5/CASA_3_1_5_register_429.png) | Staging sixth rapid POST /users/register → 429 (copy of 1.1.1 capture). |

### Portal comment

```
Authenticated APIs use Authorization Bearer, not a cookie session. Login returns JWTs in JSON and sets no Set-Cookie, so a cross-site form cannot send the session. CORS allowlists the SPA origin; a foreign Origin does not receive Access-Control-Allow-Origin. Unauthenticated register is limited to 5 requests per minute per IP. Official ADA ZAP scans (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report Absence of Anti-CSRF Tokens. We do not ship a synchronizer CSRF cookie.
```

---

## 3.1.6 — Directory browsing disabled

**ADA:** directory browsing shall be disabled unless deliberately desired (ASVS 4.3.2). AL1 evidence is ADA DAST. Verification: the scan shall not identify Burp **6291712**. Official scans were ZAP (SPA plugin **0** = FAIL).

**Claimed controls**

- SPA is hashed Vite assets on CloudFront (S3 via OAC). Not Apache/nginx autoindex.
- Production S3 `velvet-elves-prod-frontend-388482955098` (us-east-2, 31 Aug 2026, owner-captured): **Block all public access = On** (all four ACL/policy blocks).
- Staging 31 Aug 2026: `GET /assets/`, `/static/`, and a missing hashed JS file return the **SPA HTML shell**, not `Index of /` or S3 `ListBucketResult`.
- API does not mount `StaticFiles`. Staging `GET /`, `/api/v1/`, `/static/` → JSON **404**.
- Official ZAP SPA `10f54abf`, API `a9d78f05`, auth `33afa2aa` did not list Directory Browsing.

**Do not claim:** missing `/assets/*` returns 403 on staging (it returns the SPA shell); a CloudFront OAC console shot (optional, not captured); that Burp 6291712 ran.

**Helpers:** `casa_auth_qa/render_casa_316_pages.py`, `casa_316_list.py`. Do **not** attach `/login`. Do **not** recapture ZAP UI or the AWS console.

### Images

| File | Description |
| --- | --- |
| [`tac_images/3.1.6/CASA_3_1_6_page1.png`](tac_images/3.1.6/CASA_3_1_6_page1.png) | Written evidence page 1 of 2. CloudFront SPA; S3 Block public access; API JSON 404; ZAP. |
| [`tac_images/3.1.6/CASA_3_1_6_page2.png`](tac_images/3.1.6/CASA_3_1_6_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/3.1.6/CASA_3_1_6_code.png`](tac_images/3.1.6/CASA_3_1_6_code.png) | SPA rewrite function; API has no StaticFiles. |
| [`tac_images/3.1.6/CASA_3_1_6_zap.png`](tac_images/3.1.6/CASA_3_1_6_zap.png) | Official ADA ZAP directory-browsing rule excerpt. Not a ZAP product screenshot. |
| [`tac_images/3.1.6/CASA_3_1_6_nolist.png`](tac_images/3.1.6/CASA_3_1_6_nolist.png) | Staging SPA prefixes = HTML shell; API prefixes = JSON 404. |
| [`tac_images/3.1.6/CASA_3_1_6_s3_block.png`](tac_images/3.1.6/CASA_3_1_6_s3_block.png) | Production S3 Permissions: `velvet-elves-prod-frontend-388482955098`, Block all public access **On**. No object listing. No access keys. |

### Portal comment

```
Directory browsing is disabled. The SPA is hashed CloudFront assets (S3 origin via OAC), not an Apache or nginx autoindex. Production bucket velvet-elves-prod-frontend-388482955098 has Block all public access On. Staging GET /assets/, /static/, and a missing hashed JS file return the SPA HTML shell, not Index of / or an S3 ListBucketResult. The API does not mount static files; GET /, /api/v1/, and /static/ return JSON 404. Official ADA ZAP scans (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report Directory Browsing. We did not run Burp 6291712.
```

---

## 3.2.1 — OAuth authorization code + PKCE

**ADA:** use only recommended OAuth 2.0 flows (authorization code, or authorization code + PKCE). Do not use Implicit or Resource Owner Password Credentials. AL1: written description plus evidence of which flow is used.

**Claimed controls**

- Google / Microsoft **sign-in**: `POST /users/oauth/{provider}/start` → PKCE S256 on Supabase `/auth/v1/authorize`; exchange sends `code_verifier`.
- Gmail, Outlook, Google Calendar, DocuSign: `response_type=code` + `code_challenge_method=S256`.
- Email/password login is Supabase `sign_in_with_password`, not an OAuth password grant to Google.
- Staging 31 Aug 2026: `POST /users/oauth/google/start` → **200** with `s256` (flow not completed). Unsigned `POST /integrations/gmail/authorize-url` → **401**.
- Production Google Cloud OAuth client **Velvet Elves API – production** (31 Aug 2026, owner-captured, secret redacted): type **Web application**; authorized redirect URIs are production Gmail callback, Google Calendar callback, and Supabase Auth `/auth/v1/callback`. Authorized JavaScript origins are empty.

**Do not claim:** implicit flow; Google ROPC; a completed consent this session; that this GCP shot proves PKCE (PKCE is in the app/Supabase start URL); that the client secret is shown.

**Helpers:** `casa_auth_qa/render_casa_321_pages.py`, `casa_321_pkce.py`. Do **not** attach `/login`. Do **not** recapture Google Cloud Console or accounts.google.com. Do **not** complete an OAuth exchange.

### Images

| File | Description |
| --- | --- |
| [`tac_images/3.2.1/CASA_3_2_1_page1.png`](tac_images/3.2.1/CASA_3_2_1_page1.png) | Written evidence page 1 of 2. Sign-in PKCE; mailbox/DocuSign code+S256. |
| [`tac_images/3.2.1/CASA_3_2_1_page2.png`](tac_images/3.2.1/CASA_3_2_1_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/3.2.1/CASA_3_2_1_code.png`](tac_images/3.2.1/CASA_3_2_1_code.png) | oauth_service.py and gmail_provider.py PKCE params. |
| [`tac_images/3.2.1/CASA_3_2_1_tests.png`](tac_images/3.2.1/CASA_3_2_1_tests.png) | Named tests for encrypted PKCE state and tampered-state 400. |
| [`tac_images/3.2.1/CASA_3_2_1_pkce.png`](tac_images/3.2.1/CASA_3_2_1_pkce.png) | Staging Google start URL has s256; Gmail authorize-url unsigned 401. |
| [`tac_images/3.2.1/CASA_3_2_1_gcp_client.png`](tac_images/3.2.1/CASA_3_2_1_gcp_client.png) | GCP: production **Web application** client; HTTPS Gmail, Calendar, and Supabase Auth redirect URIs. Client ID remainder and client secret redacted. |

### Portal comment

```
Velvet Elves OAuth is authorization code with PKCE (S256). Google and Microsoft sign-in start at POST /users/oauth/{provider}/start and pass code_challenge to Supabase /auth/v1/authorize. Gmail, Outlook, Calendar, and DocuSign authorize URLs set response_type=code plus code_challenge_method=S256. There is no implicit flow and no resource-owner password grant to those providers. The production Google Cloud OAuth client is a Web application with HTTPS Gmail, Calendar, and Supabase Auth callback URIs. Staging POST /users/oauth/google/start returned a PKCE authorize URL (s256); the flow was not completed. Unsigned POST /integrations/gmail/authorize-url returns 401.
```

---

## 3.2.2 — OAuth redirect_uri and state

**ADA:** securely validate `redirect_uri` and `state` to prevent open redirect and OAuth CSRF. AL1: written description plus evidence. WSTG-ATHZ-05 is AL2; we did not run it.

**Claimed controls**

- Sign-in `redirect_to` must match a CORS allowlisted origin (`validate_redirect_to`). Foreign host → **400**.
- Sign-in `state` is Fernet (10-minute TTL). Tampered or mismatched state → **400** `Invalid or expired OAuth state.`
- Gmail / Outlook / Calendar / DocuSign `redirect_uri` is server-set from configuration, not client JSON. State binds user, provider, and `redirect_uri`.
- Callback `postMessage` targets `FRONTEND_URL`, not `*`. SPA checks `isTrustedOAuthMessageOrigin`.
- Staging 31 Aug 2026: evil `redirect_to` → **400**; allowlisted SPA callback → **200** (flow not completed); garbage exchange state → **400**.
- Production Google Cloud OAuth client (same PNG as 3.2.1): authorized redirect URIs are production Gmail callback, Google Calendar callback, and Supabase Auth `/auth/v1/callback`. Client secret redacted.

**Do not claim:** WSTG-ATHZ-05; exact-path match on sign-in `redirect_to` (origin check); completed consent; that GCP listing replaces API origin checks.

**Helpers:** `casa_auth_qa/render_casa_322_pages.py`, `casa_322_deny.py`. Do **not** attach `/login`. Do **not** recapture Google Cloud Console. Do **not** complete an OAuth exchange.

### Images

| File | Description |
| --- | --- |
| [`tac_images/3.2.2/CASA_3_2_2_page1.png`](tac_images/3.2.2/CASA_3_2_2_page1.png) | Written evidence page 1 of 2. redirect_to allowlist; Fernet state; server-set integration redirect_uri; postMessage origin. |
| [`tac_images/3.2.2/CASA_3_2_2_page2.png`](tac_images/3.2.2/CASA_3_2_2_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/3.2.2/CASA_3_2_2_code.png`](tac_images/3.2.2/CASA_3_2_2_code.png) | validate_redirect_to, Fernet decode, Gmail redirect_uri from settings. |
| [`tac_images/3.2.2/CASA_3_2_2_tests.png`](tac_images/3.2.2/CASA_3_2_2_tests.png) | Named tests for tampered state, provider mismatch, and postMessage origin. |
| [`tac_images/3.2.2/CASA_3_2_2_deny.png`](tac_images/3.2.2/CASA_3_2_2_deny.png) | Staging: foreign redirect_to 400; allowlisted start 200; garbage state 400. |
| [`tac_images/3.2.2/CASA_3_2_2_gcp_client.png`](tac_images/3.2.2/CASA_3_2_2_gcp_client.png) | Same production GCP Web client as 3.2.1: registered HTTPS redirect URIs. Secret redacted. |

### Portal comment

```
OAuth redirect_uri and state are validated to prevent open redirect and OAuth CSRF. Google and Microsoft sign-in redirect_to must match an allowlisted SPA origin; a foreign origin returns 400. Sign-in state is a Fernet token with a 10-minute TTL; a forged state on POST /users/oauth/google/exchange returns 400 Invalid or expired OAuth state. Gmail, Outlook, Calendar, and DocuSign redirect_uri is set by the API from configuration, not by the client. Google Cloud lists the production Gmail, Calendar, and Supabase Auth callback URIs as authorized redirects. Integration state binds user, provider, and redirect_uri. Callback postMessage targets FRONTEND_URL, not *. Staging: foreign redirect_to 400; garbage state 400.
```

---

## 3.3.1 — Admin MFA on the platform console

**ADA:** application administrative interfaces shall enforce MFA for administrative accounts. Cloud infrastructure consoles are out of this check.

**Claimed controls**

- Administrative interface = platform console (`/platform/*`, `/api/v1/platform/*`).
- `require_platform_admin`: `is_platform_admin` + JWT `aal2` + live verified TOTP. `PLATFORM_ADMIN_MFA_REQUIRED` defaults true.
- Login of an enrolled account returns `mfa_required` (AAL1, no refresh) until `POST /users/mfa/verify`.
- SPA `PlatformMfaGate` blocks the console until a code (or enrollment in Security).
- Staging and production UI: two-step login prompt; console code gate; Security authenticator on.
- Staging unsigned `GET /platform/users`, `GET /platform/registrations`, and `GET /users/mfa/factors` → **401**.

**Do not claim:** MFA for all users or all tenant Admins; GCP/AWS MFA; that the emergency env flag cannot be turned off.

**Helpers:** `casa_auth_qa/render_casa_331_pages.py`, `casa_331_deny.py`, `casa_331_prod_enroll_shots.mjs` (production recapture only; does not write enroll/login extras). Folder contains **only** the 10 upload files. Production `prod_mfa_prompt` / `prod_security_on` recaptured 31 Aug 2026 after a temporary TOTP enroll; the QA authenticator was then turned off so password login still works. Re-enroll in your own authenticator app before TAC reviews production live.

### Images

| File | Description |
| --- | --- |
| [`tac_images/3.3.1/CASA_3_3_1_page1.png`](tac_images/3.3.1/CASA_3_3_1_page1.png) | Written evidence page 1 of 2. Platform console MFA; aal2 gate. |
| [`tac_images/3.3.1/CASA_3_3_1_page2.png`](tac_images/3.3.1/CASA_3_3_1_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/3.3.1/CASA_3_3_1_code.png`](tac_images/3.3.1/CASA_3_3_1_code.png) | require_platform_admin aal2 + TOTP check. |
| [`tac_images/3.3.1/CASA_3_3_1_tests.png`](tac_images/3.3.1/CASA_3_3_1_tests.png) | Named tests for aal1 deny, aal2 allow, stale aal2, login mfa_required. |
| [`tac_images/3.3.1/CASA_3_3_1_deny.png`](tac_images/3.3.1/CASA_3_3_1_deny.png) | Staging unsigned platform/MFA GETs return 401. |
| [`tac_images/3.3.1/CASA_3_3_1_stage_mfa_prompt.png`](tac_images/3.3.1/CASA_3_3_1_stage_mfa_prompt.png) | Staging login two-step verification. |
| [`tac_images/3.3.1/CASA_3_3_1_stage_platform_code.png`](tac_images/3.3.1/CASA_3_3_1_stage_platform_code.png) | Staging platform console code gate. |
| [`tac_images/3.3.1/CASA_3_3_1_stage_security_on.png`](tac_images/3.3.1/CASA_3_3_1_stage_security_on.png) | Staging Security: authenticator app is on. |
| [`tac_images/3.3.1/CASA_3_3_1_prod_mfa_prompt.png`](tac_images/3.3.1/CASA_3_3_1_prod_mfa_prompt.png) | Production login two-step verification. |
| [`tac_images/3.3.1/CASA_3_3_1_prod_security_on.png`](tac_images/3.3.1/CASA_3_3_1_prod_security_on.png) | Production Security: authenticator app is on. |

### Portal comment

```
The application administrative interface is the platform console (/api/v1/platform/*). Those routes require is_platform_admin plus a JWT aal2 claim and a live verified TOTP factor (PLATFORM_ADMIN_MFA_REQUIRED defaults true). Login of an enrolled admin returns mfa_required until the authenticator code is verified. The SPA PlatformMfaGate blocks the console until a code is entered. Staging and production both show the two-step prompt and Security authenticator app is on. Unsigned GET /platform/users returns 401. Tenant Admin is a workspace role and is not this interface; MFA is not required for all users.
```

---

## 4.1.1 — TLS 1.2+ on production SPA and API

**ADA:** enforce TLS for all connections and default to TLS 1.2+. AL1 named evidence is a **Qualys SSL Labs PDF**, typically grade **B or higher** (NIST SP.800-52r2).

**Claimed controls**

- Qualys SSL Labs 31 Aug 2026: **A+** on every tested endpoint of `app.velvetelves.com` and `api.prod.velvetelves.com`. TLS 1.3 and 1.2 Yes; TLS 1.1, TLS 1.0, SSL 3, SSL 2 No.
- SPA CloudFront: HTTP **301** to HTTPS, HSTS `max-age=31536000; includeSubDomains`.
- API ALB: HTTPS HSTS from `SecurityHeadersMiddleware`. Certificates: Amazon ACM (public).

**Do not claim:** that the API is HTTPS-only (HTTP `GET /api/v1/health` returned **200** JSON); that the API has no Qualys-flagged weak ciphers (two TLS 1.2 CBC suites are WEAK; grade is still A+); HttpOnly session cookies.

**Helpers:** `casa_auth_qa/render_casa_411_pages.py`, `casa_411_tls.py`, `casa_411_ssllabs.mjs` (one host at a time), `casa_411_caption_ssllabs.py` (run once after a fresh protocol shot).

### Images

| File | Description |
| --- | --- |
| [`tac_images/4.1.1/CASA_4_1_1_page1.png`](tac_images/4.1.1/CASA_4_1_1_page1.png) | Written evidence page 1 of 2. TLS termination, Qualys A+, HTTP port 80, HSTS. |
| [`tac_images/4.1.1/CASA_4_1_1_page2.png`](tac_images/4.1.1/CASA_4_1_1_page2.png) | Written evidence page 2 of 2. AL1 mapping. API HTTP listener not claimed as HTTPS-only. |
| [`tac_images/4.1.1/CASA_4_1_1_code.png`](tac_images/4.1.1/CASA_4_1_1_code.png) | FastAPI HSTS middleware; CloudFront TLSv1.2_2021; ALB TLS 1.3/1.2 policy. |
| [`tac_images/4.1.1/CASA_4_1_1_tests.png`](tac_images/4.1.1/CASA_4_1_1_tests.png) | Named HSTS tests plus live TLS/Qualys notes. |
| [`tac_images/4.1.1/CASA_4_1_1_tls.png`](tac_images/4.1.1/CASA_4_1_1_tls.png) | Live production handshake: TLS 1.3/1.2, HSTS, SPA 301, API HTTP health 200. |
| [`tac_images/4.1.1/CASA_4_1_1_ssllabs_app.png`](tac_images/4.1.1/CASA_4_1_1_ssllabs_app.png) | Qualys SSL Labs: app.velvetelves.com, all endpoints A+. |
| [`tac_images/4.1.1/CASA_4_1_1_ssllabs_app_protocols.png`](tac_images/4.1.1/CASA_4_1_1_ssllabs_app_protocols.png) | Qualys: SPA TLS 1.3/1.2 Yes; TLS 1.1/1.0 and SSL 3/2 No. |
| [`tac_images/4.1.1/CASA_4_1_1_ssllabs_api.png`](tac_images/4.1.1/CASA_4_1_1_ssllabs_api.png) | Qualys SSL Labs: api.prod.velvetelves.com, both endpoints A+. |
| [`tac_images/4.1.1/CASA_4_1_1_ssllabs_api_protocols.png`](tac_images/4.1.1/CASA_4_1_1_ssllabs_api_protocols.png) | Qualys: API TLS 1.3/1.2 Yes; TLS 1.1/1.0 and SSL 3/2 No. |

### Portal comment

```
The production SPA (app.velvetelves.com) and API (api.prod.velvetelves.com) terminate TLS on CloudFront and an ALB. Qualys SSL Labs on 31 Aug 2026 graded every tested endpoint A+ (TLS 1.3 and 1.2 enabled; TLS 1.1, TLS 1.0, SSL 3, and SSL 2 disabled). HTTPS responses send Strict-Transport-Security: max-age=31536000; includeSubDomains. HTTP on the SPA returns 301 to HTTPS. HTTP on the API currently reaches FastAPI (GET /api/v1/health returned 200 JSON); that listener is not claimed as HTTPS-only. Certificates are Amazon ACM.
```

---

## 4.1.2 — Trusted TLS certificates

**ADA:** connections to and from the server shall use trusted TLS certificates. AL1 named evidence is the same Qualys SSL Labs PDF as 4.1.1 (grade B or higher).

**Claimed controls**

- Qualys SSL Labs 31 Aug 2026: **A+** on `app.velvetelves.com` and `api.prod.velvetelves.com`. Chain is Amazon RSA 2048 + Amazon Root CA 1.
- Live OS trust store verified both hostnames. Not self-signed.
- SPA SAN includes `app.velvetelves.com` (CN is `app.stage.velvetelves.com`; one ACM cert covers both SPA names). API CN/SAN is `api.prod.velvetelves.com`.
- Currently valid (SPA through 13 Jan 2027, API through 14 Jan 2027). Wrong SNI/name does not complete a trusted handshake.
- Backend has no `verify=False` / `CERT_NONE`.
- AWS ACM us-east-2 (31 Aug 2026, owner-captured): `api.prod.velvetelves.com` is **Amazon issued**, status **Issued**, **in use**, not after **14 Jan 2027**. DNS validation CNAME name/value redacted.
- AWS ACM us-east-1 (31 Aug 2026, owner-captured): one cert covers **`app.stage.velvetelves.com`** and **`app.velvetelves.com`**, **Amazon issued**, **Issued**, **in use**, not after **13 Jan 2027**. CNAME name/value redacted.

**Do not claim:** a production-only SPA certificate (SAN also includes staging); SSL Labs of outbound hosts; that the API is HTTPS-only on port 80.

**Helpers:** `casa_auth_qa/render_casa_412_pages.py`, `casa_412_certs.py` (copies Qualys PNGs from 4.1.1). Do **not** recapture ssllabs.com or the ACM console. Folder is at the **10-file** portal cap.

### Images

| File | Description |
| --- | --- |
| [`tac_images/4.1.2/CASA_4_1_2_page1.png`](tac_images/4.1.2/CASA_4_1_2_page1.png) | Written evidence page 1 of 2. Qualys A+, live ACM peer certs, ACM console. |
| [`tac_images/4.1.2/CASA_4_1_2_page2.png`](tac_images/4.1.2/CASA_4_1_2_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/4.1.2/CASA_4_1_2_code.png`](tac_images/4.1.2/CASA_4_1_2_code.png) | Live cert fields; no verify=False; ACM on CloudFront/ALB. |
| [`tac_images/4.1.2/CASA_4_1_2_cert.png`](tac_images/4.1.2/CASA_4_1_2_cert.png) | Live production handshake: Amazon ACM, SAN match, currently valid, not self-signed. |
| [`tac_images/4.1.2/CASA_4_1_2_ssllabs_app.png`](tac_images/4.1.2/CASA_4_1_2_ssllabs_app.png) | Qualys: app.velvetelves.com all endpoints A+ (same scan as 4.1.1). |
| [`tac_images/4.1.2/CASA_4_1_2_ssllabs_app_chain.png`](tac_images/4.1.2/CASA_4_1_2_ssllabs_app_chain.png) | Qualys SPA chain: Amazon RSA 2048 M01, Amazon Root CA 1. |
| [`tac_images/4.1.2/CASA_4_1_2_ssllabs_api.png`](tac_images/4.1.2/CASA_4_1_2_ssllabs_api.png) | Qualys: api.prod.velvetelves.com both endpoints A+. |
| [`tac_images/4.1.2/CASA_4_1_2_ssllabs_api_chain.png`](tac_images/4.1.2/CASA_4_1_2_ssllabs_api_chain.png) | Qualys API chain: Amazon RSA 2048 M04, Amazon Root CA 1. |
| [`tac_images/4.1.2/CASA_4_1_2_acm.png`](tac_images/4.1.2/CASA_4_1_2_acm.png) | ACM us-east-2: `api.prod.velvetelves.com` Amazon issued, Issued, in use, valid through 14 Jan 2027. CNAME values redacted. No private key. |
| [`tac_images/4.1.2/CASA_4_1_2_acm_spa.png`](tac_images/4.1.2/CASA_4_1_2_acm_spa.png) | ACM us-east-1: `app.stage.velvetelves.com` + `app.velvetelves.com` Amazon issued, Issued, in use, valid through 13 Jan 2027. CNAME values redacted. No private key. |

### Portal comment

```
Production TLS certificates are public Amazon ACM, not self-signed. Qualys SSL Labs on 31 Aug 2026 graded app.velvetelves.com and api.prod.velvetelves.com A+; the chain is Amazon RSA 2048 with Amazon Root CA 1. A live handshake with the OS trust store verified both hostnames. ACM in us-east-1 lists one Amazon-issued certificate covering app.stage.velvetelves.com and app.velvetelves.com, status Issued, in use, valid through 13 January 2027. ACM in us-east-2 lists the api.prod.velvetelves.com certificate as Amazon issued, Issued, in use, valid through 14 January 2027. Both leaves are currently valid. A hostname mismatch does not complete a trusted handshake.
```

---

## 4.1.3 — No weak crypto that meaningfully impacts confidentiality

**ADA:** describe encryption, hashing, and MAC/HMAC (algorithms, key size, IV, key management). 112-bit baseline.

**Claimed controls**

- Tokens and PII: Fernet AES-128-CBC + HMAC-SHA256. `ENCRYPTION_KEY` in Secrets Manager. Production fails closed if missing. Fresh 128-bit IV per token.
- Passwords: GoTrue salted bcrypt (not in app tables).
- Capability secrets and fingerprints: SHA-256. Webhooks: HMAC-SHA256. Session JWT: ES256/HS256.
- SHA-1 only as a 16-hex intake proposal id (Fluid F052 Low). Not a password KDF or token MAC.

**Do not claim:** AES-256; a completed key-rotation drill; that SHA-1 is unused; Fernet keys or production hashes in screenshots; that the API has no Qualys-flagged TLS CBC suites (see 4.1.1).

**Helpers:** `casa_auth_qa/render_casa_413_pages.py`, `casa_413_fernet.py` (ephemeral key only).

### Images

| File | Description |
| --- | --- |
| [`tac_images/4.1.3/CASA_4_1_3_page1.png`](tac_images/4.1.3/CASA_4_1_3_page1.png) | Written evidence page 1 of 2. Encryption, hashing, MAC, SHA-1 label. |
| [`tac_images/4.1.3/CASA_4_1_3_page2.png`](tac_images/4.1.3/CASA_4_1_3_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/4.1.3/CASA_4_1_3_code.png`](tac_images/4.1.3/CASA_4_1_3_code.png) | Fernet encrypt/decrypt; production requires ENCRYPTION_KEY. |
| [`tac_images/4.1.3/CASA_4_1_3_sha1.png`](tac_images/4.1.3/CASA_4_1_3_sha1.png) | `_proposal_id` SHA-1 truncated to 16 hex. |
| [`tac_images/4.1.3/CASA_4_1_3_tests.png`](tac_images/4.1.3/CASA_4_1_3_tests.png) | Named Fernet state tests; garbage rejected. |
| [`tac_images/4.1.3/CASA_4_1_3_fernet.png`](tac_images/4.1.3/CASA_4_1_3_fernet.png) | Ephemeral Fernet round-trip; tampered token InvalidToken. Production key not used. |

### Portal comment

```
Confidential data uses Fernet (AES-128-CBC plus HMAC-SHA256) with a 256-bit key stored as ENCRYPTION_KEY in AWS Secrets Manager. Production fails to start if the key is missing. Fernet issues a fresh 128-bit IV per token. That covers OAuth tokens, selected PII, and OAuth state. User passwords are salted bcrypt in Supabase GoTrue, not in application tables. Capability secrets are stored as SHA-256 hashes. Webhooks use HMAC-SHA256. Session JWTs are ES256 or HS256. SHA-1 appears only as a 16-character intake proposal id (not a password or token MAC). No encryption keys are attached.
```

---

## 4.1.4 — Cryptographic failures fail closed

**ADA:** crypto failures must not disclose operation state or enable a padding oracle. User-facing errors stay vague and consistent.

**Claimed controls**

- Fernet HMAC is checked before AES-CBC. HMAC flip and ciphertext flip both `InvalidToken`. Display helpers return empty/None (no `gAAAA` leak).
- OAuth state decode returns None → **400** `Invalid or expired OAuth state.`
- JWT `JWTError` → **401** `Could not validate credentials.`
- Staging 31 Aug 2026: garbage Bearer **401**; garbage OAuth state **400**.

**Do not claim:** a WSTG-CRYP-02 lab scan; that every historical row is ciphertext.

**Helpers:** `casa_auth_qa/render_casa_414_pages.py`, `casa_414_fail.py`

### Images

| File | Description |
| --- | --- |
| [`tac_images/4.1.4/CASA_4_1_4_page1.png`](tac_images/4.1.4/CASA_4_1_4_page1.png) | Written evidence page 1 of 2. Fernet, OAuth state, JWT, padding-oracle note. |
| [`tac_images/4.1.4/CASA_4_1_4_page2.png`](tac_images/4.1.4/CASA_4_1_4_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/4.1.4/CASA_4_1_4_code.png`](tac_images/4.1.4/CASA_4_1_4_code.png) | InvalidToken, _safe_decrypt, OAuth None, JWT 401. |
| [`tac_images/4.1.4/CASA_4_1_4_tests.png`](tac_images/4.1.4/CASA_4_1_4_tests.png) | Named tests plus live HMAC/JWT/OAuth notes. |
| [`tac_images/4.1.4/CASA_4_1_4_fernet_fail.png`](tac_images/4.1.4/CASA_4_1_4_fernet_fail.png) | Ephemeral Fernet: HMAC and ciphertext flips both InvalidToken. |
| [`tac_images/4.1.4/CASA_4_1_4_deny.png`](tac_images/4.1.4/CASA_4_1_4_deny.png) | Staging: garbage JWT 401; garbage OAuth state 400. |

### Portal comment

```
Cryptographic failures fail closed and do not return plaintext. Fernet verifies HMAC-SHA256 before AES-CBC decrypt; a bad MAC and a flipped ciphertext byte both raise InvalidToken, mapped to a generic Decryption failed error. Display helpers return empty on any decrypt exception so ciphertext is not shown in the UI. OAuth state decode returns None on InvalidToken; exchange is 400 Invalid or expired OAuth state. Invalid JWTs raise JWTError and become 401 Could not validate credentials. Staging: GET /users/me with Bearer not-a-jwt is 401; POST /users/oauth/google/exchange with garbage state is 400.
```

---

## 5.1.1 — Protect against HTTP parameter pollution

**ADA:** AL1 evidence is ADA DAST. Verification: scan shall **not** identify Burp **5248000** (client-side HPP reflected) or **5248001** (stored). WSTG-INPV-04 is AL2.

**Claimed controls**

- Official ADA ZAP (SPA `10f54abf`, API `a9d78f05`, auth `33afa2aa`): plugin **20014** HTTP Parameter Pollution is FAIL on the SPA conf and WARN on the API conf. Alert lists did not include it.
- FastAPI typed Query/path scalars. No `request.query_params.getlist`. Duplicate keys are not concatenated.
- Staging 31 Aug 2026: help search last-wins (422 vs 200); unsigned `/teams?page=1&page=2` **401**; duplicate pay tokens **403**.

**Do not claim:** that Burp 5248000/5248001 ran; WSTG-INPV-04; that every param is a scalar (`list[str] = Query` exists on some authenticated filters); that the SPA spider crawled authenticated routes.

**Helpers:** `casa_auth_qa/render_casa_511_pages.py`, `casa_511_hpp.py`

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.1/CASA_5_1_1_page1.png`](tac_images/5.1.1/CASA_5_1_1_page1.png) | Written evidence page 1 of 2. Official ZAP 20014, typed FastAPI params, staging last-wins, SPA URLSearchParams.get. |
| [`tac_images/5.1.1/CASA_5_1_1_page2.png`](tac_images/5.1.1/CASA_5_1_1_page2.png) | Written evidence page 2 of 2. AL1 mapping. Burp not run. SPA spider limited to /, robots, sitemap. |
| [`tac_images/5.1.1/CASA_5_1_1_code.png`](tac_images/5.1.1/CASA_5_1_1_code.png) | FastAPI Query scalars for teams page, help search q, public pay token. No getlist. |
| [`tac_images/5.1.1/CASA_5_1_1_zap.png`](tac_images/5.1.1/CASA_5_1_1_zap.png) | Official ADA ZAP 20014 FAIL/WARN; DAST_SUMMARY alert lists did not include HPP. Pillow summary, not ZAP UI. |
| [`tac_images/5.1.1/CASA_5_1_1_hpp.png`](tac_images/5.1.1/CASA_5_1_1_hpp.png) | Staging: duplicate health keys 200; help search last-wins 422 then 200; unsigned teams 401; duplicate pay tokens 403. |

### Portal comment

```
Official ADA ZAP scans of staging (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report HTTP Parameter Pollution (ZAP plugin 20014; SPA conf FAIL, API conf WARN). We did not run Burp 5248000 or 5248001. FastAPI binds query and path parameters as typed scalars; the backend does not call getlist. Duplicate keys take one value and are not concatenated. Staging public help search: q=ok plus a 161-character q is 422 on the last value; a long q plus q=ok is 200. Unsigned GET /teams?page=1&page=2 is 401. Duplicate public payment tokens are 403. Session is Authorization Bearer, not a query parameter. WSTG-INPV-04 is AL2 and was not run.
```

---

## 5.1.2 — URL redirects limited to allowlisted URLs

**ADA:** AL1 evidence is ADA DAST. Verification: scan shall **not** identify Burp **5243136**, **5243137**, **5243152**, **5243153**, or **5243154** (open redirection). WSTG-CLNT-04 is AL2.

**Claimed controls**

- Official ADA ZAP (SPA `10f54abf`, API `a9d78f05`, auth `33afa2aa`): plugin **20019** External Redirect is FAIL on the SPA conf and WARN on the API conf. Alert lists did not include it.
- OAuth `redirect_to` origin allowlist (`CORS_ORIGINS`). Foreign origin **400**.
- Password-reset disallowed `redirect_to` is ignored (**202**, no foreign Location).
- Ad click 302 uses a stored `click_url`; unknown hook **404**. SPA `?next=` to a foreign host has no `Location`.

**Do not claim:** that Burp 5243136–5243154 ran; WSTG-CLNT-04; that password-reset foreign `redirect_to` is 400; that ad click URLs are CORS origins.

**Helpers:** `casa_auth_qa/render_casa_512_pages.py`, `casa_512_deny.py`

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.2/CASA_5_1_2_page1.png`](tac_images/5.1.2/CASA_5_1_2_page1.png) | Written evidence page 1 of 2. Official ZAP 20019, allowlists, ad click, SPA restore, staging measurements. |
| [`tac_images/5.1.2/CASA_5_1_2_page2.png`](tac_images/5.1.2/CASA_5_1_2_page2.png) | Written evidence page 2 of 2. AL1 mapping. Burp not run. SPA spider limited to /, robots, sitemap. |
| [`tac_images/5.1.2/CASA_5_1_2_code.png`](tac_images/5.1.2/CASA_5_1_2_code.png) | validate_redirect_to 400; postMessage FRONTEND_URL; ad click stored URL; SPA paths must start with /. |
| [`tac_images/5.1.2/CASA_5_1_2_zap.png`](tac_images/5.1.2/CASA_5_1_2_zap.png) | Official ADA ZAP 20019 FAIL/WARN; DAST_SUMMARY alert lists did not include External Redirect. Pillow summary, not ZAP UI. |
| [`tac_images/5.1.2/CASA_5_1_2_tests.png`](tac_images/5.1.2/CASA_5_1_2_tests.png) | Named tests plus live 400/202/404/200 notes. |
| [`tac_images/5.1.2/CASA_5_1_2_deny.png`](tac_images/5.1.2/CASA_5_1_2_deny.png) | Staging: foreign OAuth redirect_to 400; password-reset 202 no Location; unknown ad click 404; SPA ?next= 200 no Location. |

### Portal comment

```
Official ADA ZAP scans of staging (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report External Redirect (ZAP plugin 20019; SPA conf FAIL, API conf WARN). We did not run Burp 5243136, 5243137, 5243152, 5243153, or 5243154. OAuth sign-in redirect_to must match a CORS origin; a foreign origin is 400. Password-reset redirect_to that is not allowlisted is ignored. Ad click 302 uses a stored click_url, not a query parameter; an unknown hook is 404. OAuth callback postMessage targets FRONTEND_URL, not *. SPA return URLs must start with /. Staging: POST /users/oauth/google/start with https://evil.example/steal is 400 with no Location; GET /ads/{uuid}/click is 404 with no Location; SPA GET ?next=https://evil.example is 200 with no Location to that host. WSTG-CLNT-04 is AL2 and was not run.
```

---

---

## 5.1.3 — Avoid eval / dynamic code execution

**ADA:** AL1 DAST. Burp 1051904 / 1052160 / 1052416 / 1052432 / 1051648 / 1052672 / 1052448 shall not be identified.

**Claimed:** Official ZAP 90019/20018 not in DAST_SUMMARY. No eval/exec on user input. Staging health extra query still 200.

**Missing:** Burp UI; ZAP UI; WSTG-INPV-11.

**Helpers:** `render_casa_rest.py`, `casa_rest_live.py`

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.3/CASA_5_1_3_eval_page1.png`](tac_images/5.1.3/CASA_5_1_3_eval_page1.png) | Write-up |
| [`tac_images/5.1.3/CASA_5_1_3_eval_page2.png`](tac_images/5.1.3/CASA_5_1_3_eval_page2.png) | AL1 mapping |
| [`tac_images/5.1.3/CASA_5_1_3_eval_code.png`](tac_images/5.1.3/CASA_5_1_3_eval_code.png) | No eval/exec |
| [`tac_images/5.1.3/CASA_5_1_3_eval_zap.png`](tac_images/5.1.3/CASA_5_1_3_eval_zap.png) | ZAP 90019 Pillow |
| [`tac_images/5.1.3/CASA_5_1_3_probe.png`](tac_images/5.1.3/CASA_5_1_3_probe.png) | Staging health extra query 200 |

### Portal comment

```
Official ADA ZAP scans of staging (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report server-side code injection (ZAP 90019 FAIL, 20018 FAIL). We did not run Burp 1051904, 1052432, or 1052448. The API does not call eval or exec on user input. The SPA source has no eval or new Function. Email templates substitute named {{token}} keys from a mapping. Staging GET /health with an import-looking query is still 200 JSON. WSTG-INPV-11 is AL2 and was not run.
```

---

## 5.1.4 — Template injection

**ADA:** AL1 DAST. Burp 1052800 shall not be identified.

**Claimed:** No Jinja of user templates; {{name}} mapping only. ZAP has no SSTI rule; 90025 WARN not in alerts. Staging `GET /api/v1/health?q={{7*7}}` → **200** JSON health (`status ok`); body is **not** `49`.

**Missing:** Burp 1052800; WSTG-INPV-18.

**Do not claim:** that this probe tested email/vendor Jinja rendering (health ignores extra query); that Burp 1052800 ran.

**Helpers:** `casa_auth_qa/casa_514_probe.py` (also `casa_rest_live.py` `probe_514`). Do **not** attach `/login`.

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.4/CASA_5_1_4_ssti_page1.png`](tac_images/5.1.4/CASA_5_1_4_ssti_page1.png) | Write-up |
| [`tac_images/5.1.4/CASA_5_1_4_ssti_page2.png`](tac_images/5.1.4/CASA_5_1_4_ssti_page2.png) | AL1 mapping |
| [`tac_images/5.1.4/CASA_5_1_4_ssti_code.png`](tac_images/5.1.4/CASA_5_1_4_ssti_code.png) | _substitute mapping.get |
| [`tac_images/5.1.4/CASA_5_1_4_ssti_zap.png`](tac_images/5.1.4/CASA_5_1_4_ssti_zap.png) | No SSTI plugin; 90025 WARN |
| [`tac_images/5.1.4/CASA_5_1_4_probe.png`](tac_images/5.1.4/CASA_5_1_4_probe.png) | Staging GET /health?q={{7*7}} → 200 JSON health, not 49. |

### Portal comment

```
Official ADA ZAP scans did not report template injection or expression-language injection. The ADA ZAP conf has no dedicated SSTI rule (90025 EL is WARN). APIs return JSON. Email and vendor copy replace named {{token}} keys from a mapping; unknown keys are empty. We do not render user Jinja. Staging GET /api/v1/health with q={{7*7}} returned 200 JSON health (status ok); the body is not 49 and the extra query is ignored. We did not run Burp 1052800. WSTG-INPV-18 is AL2 and was not run.
```

---

## 5.1.5 — SSRF

**ADA:** AL1 DAST. Burp 1051136 / 3146240 / 3146256 shall not be identified.

**Claimed:** No SSRF plugin in ADA ZAP conf; alerts did not list SSRF. assert_safe_url rejects loopback/metadata/private. Unsigned webhook POST 401. Authenticated metadata URL 400.

**Missing:** Burp OOB plugins; WSTG-INPV-19.

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.5/CASA_5_1_5_ssrf_page1.png`](tac_images/5.1.5/CASA_5_1_5_ssrf_page1.png) | Write-up |
| [`tac_images/5.1.5/CASA_5_1_5_ssrf_page2.png`](tac_images/5.1.5/CASA_5_1_5_ssrf_page2.png) | AL1 mapping |
| [`tac_images/5.1.5/CASA_5_1_5_ssrf_code.png`](tac_images/5.1.5/CASA_5_1_5_ssrf_code.png) | assert_safe_url |
| [`tac_images/5.1.5/CASA_5_1_5_ssrf_zap.png`](tac_images/5.1.5/CASA_5_1_5_ssrf_zap.png) | No SSRF plugin |
| [`tac_images/5.1.5/CASA_5_1_5_ssrf.png`](tac_images/5.1.5/CASA_5_1_5_ssrf.png) | Local rejects + unsigned 401 |
| [`tac_images/5.1.5/CASA_5_1_5_ssrf_auth.png`](tac_images/5.1.5/CASA_5_1_5_ssrf_auth.png) | Authenticated metadata URL 400 |

### Portal comment

```
Official ADA ZAP scans did not report SSRF, OOB resource load, or external service interaction. The ADA ZAP conf has no dedicated SSRF plugin. Tenant webhook and ad click URLs pass assert_safe_url (http/https only; no localhost, metadata, or private addresses). Staging unsigned POST /integrations/webhooks with a metadata URL is 401. Authenticated POST with http://169.254.169.254/latest/meta-data/ is 400 (URL isn't allowed). We did not run Burp 1051136, 3146240, or 3146256. WSTG-INPV-19 is AL2 and was not run.
```

---

## 5.1.6 — XML / XPath injection

**ADA:** AL1 DAST. Burp 1050368 / 1050112 / 1049600 / 2098016-18 shall not be identified.

**Claimed:** ZAP 90023/90021 not in alerts. No lxml/etree. XML login body rejected.

**Missing:** Burp XML plugins; WSTG-INPV-07/09.

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.6/CASA_5_1_6_xml_page1.png`](tac_images/5.1.6/CASA_5_1_6_xml_page1.png) | Write-up |
| [`tac_images/5.1.6/CASA_5_1_6_xml_page2.png`](tac_images/5.1.6/CASA_5_1_6_xml_page2.png) | AL1 mapping |
| [`tac_images/5.1.6/CASA_5_1_6_xml_code.png`](tac_images/5.1.6/CASA_5_1_6_xml_code.png) | No XML parser |
| [`tac_images/5.1.6/CASA_5_1_6_xml_zap.png`](tac_images/5.1.6/CASA_5_1_6_xml_zap.png) | ZAP 90023/90021 |
| [`tac_images/5.1.6/CASA_5_1_6_xml.png`](tac_images/5.1.6/CASA_5_1_6_xml.png) | XML Content-Type on login rejected |

### Portal comment

```
Official ADA ZAP scans did not report XXE, XPath, or XML injection (ZAP 90023 FAIL, 90021 FAIL). Public APIs are JSON. The backend has no lxml, xml.etree, or xpath parser of user bodies. Staging POST /users/login with Content-Type application/xml is 400/415/422 and does not echo the XML. We did not run Burp 1050368, 1050112, or 1049600. WSTG-INPV-07 and INPV-09 are AL2 and were not run.
```

---

## 5.1.7 — XSS

**ADA:** AL1 DAST. Burp 2097408 / 2097920 / 2097936-38 shall not be identified.

**Claimed:** OAuth XSS closed on a9d78f05. Callback does not echo script tags. Staging contact `full_name` with a script-looking string renders as React text on `/contacts` (no alert dialog; 0 executable `alert(1)` script nodes). Contact deleted after the shot (HTTP 204). CSP Mediums compensating. Auth JSON XSS Low.

**Missing:** Burp XSS plugins.

**Do not claim:** that Burp XSS plugins ran; that CSP Mediums are gone; that this one contact field covers every XSS sink; that production was tested.

**Helpers:** `casa_auth_qa/casa_517_stored.mjs` then `python casa_517_caption.py` (`QA_PASSWORD`). Do **not** attach `/login`. Do **not** leave the contact on staging.

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.7/CASA_5_1_7_xss_page1.png`](tac_images/5.1.7/CASA_5_1_7_xss_page1.png) | Write-up |
| [`tac_images/5.1.7/CASA_5_1_7_xss_page2.png`](tac_images/5.1.7/CASA_5_1_7_xss_page2.png) | AL1 mapping |
| [`tac_images/5.1.7/CASA_5_1_7_xss_code.png`](tac_images/5.1.7/CASA_5_1_7_xss_code.png) | html.escape callback |
| [`tac_images/5.1.7/CASA_5_1_7_xss_zap.png`](tac_images/5.1.7/CASA_5_1_7_xss_zap.png) | ZAP XSS plugins |
| [`tac_images/5.1.7/CASA_5_1_7_callback.png`](tac_images/5.1.7/CASA_5_1_7_callback.png) | Staging callback no script echo |
| [`tac_images/5.1.7/CASA_5_1_7_stored.png`](tac_images/5.1.7/CASA_5_1_7_stored.png) | Staging contact name is text, not a running script |

### Portal comment

```
Official unauth API ZAP a9d78f05 closed reflected XSS on OAuth callbacks (0 High). SPA 10f54abf was 0 High. Auth scan 33afa2aa reported persistent XSS in JSON at Low confidence; those responses are JSON, not HTML. CSP Mediums (img-src https:, style-src unsafe-inline) remain as compensating residuals. Staging GET gmail callback with a script in error does not put a script tag in the HTML. Staging contact full_name with a script-looking string rendered as text on /contacts (no alert dialog). That contact was deleted after the shot. We did not run Burp XSS plugins 2097408 / 2097920 / 2097936.
```

---

## 5.1.8 — SQL injection

**ADA:** AL1 DAST. Burp 1049088 / 1049104 shall not be identified.

**Claimed:** Auth ZAP SQLi High/Low is FP. Unsigned `page_size='(` is **401**, no SQL text. Authenticated replay of all **28** plugin **40018** URIs on staging (scan `33afa2aa`): **400**×4, **403**×11 (including `mfa_required` on platform routes), **422**×7, generic JSON **500**×6. None **401**. No SQLSTATE, table names, or `syntax error at`.

**Missing:** Burp SQLi; WSTG-INPV-05.

**Do not claim:** that Burp 1049088 / 1049104 ran; that 403 MFA reproduced ZAP’s 500s; that generic 500s are confirmed CWE-89; that production was scanned.

**Helpers:** `casa_auth_qa/casa_518_replay.py` (`QA_PASSWORD`; reads local gitignored ZAP XML). Do **not** attach `/login`. Do **not** print the Bearer.

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.8/CASA_5_1_8_sqli_page1.png`](tac_images/5.1.8/CASA_5_1_8_sqli_page1.png) | Write-up |
| [`tac_images/5.1.8/CASA_5_1_8_sqli_page2.png`](tac_images/5.1.8/CASA_5_1_8_sqli_page2.png) | AL1 mapping |
| [`tac_images/5.1.8/CASA_5_1_8_sqli_code.png`](tac_images/5.1.8/CASA_5_1_8_sqli_code.png) | Parameterized access |
| [`tac_images/5.1.8/CASA_5_1_8_sqli_zap.png`](tac_images/5.1.8/CASA_5_1_8_sqli_zap.png) | Auth High FP note |
| [`tac_images/5.1.8/CASA_5_1_8_replay.png`](tac_images/5.1.8/CASA_5_1_8_replay.png) | Unsigned page_size quote is 401 |
| [`tac_images/5.1.8/CASA_5_1_8_auth_replay.png`](tac_images/5.1.8/CASA_5_1_8_auth_replay.png) | All 28 plugin 40018 URIs replayed; no SQL text |

### Portal comment

```
Official unauth ZAP scans did not confirm SQL injection. Auth ZAP 33afa2aa raised SQL Injection High with Low confidence (plugin 40018 WARN on the API conf). Evidence was HTTP 500 only, no SQL error text. Staging unsigned GET /teams?page_size='( is 401 Not authenticated, not a database error. On 31 Aug 2026 we replayed all 28 plugin 40018 URIs against api.stage.velvetelves.com with a staging Bearer (value not shown). None returned 401. Responses were 400, 403 (including mfa_required on platform routes), 422 validation, or generic JSON 500 An internal server error occurred. None contained SQLSTATE, table names, or syntax error at. Queries go through SQLAlchemy / PostgREST, not client SQL strings. We did not run Burp 1049088 or 1049104. WSTG-INPV-05 is AL2 and was not run.
```

---

## 5.1.9 — OS command injection

**ADA:** AL1 DAST. Burp 1048832 shall not be identified.

**Claimed:** No subprocess/os.system. ZAP 90020 not in alerts. Staging `GET /api/v1/health?q=$(id)` → **200** JSON health (`status ok`); body is **not** command stdout.

**Missing:** Burp 1048832; WSTG-INPV-12.

**Do not claim:** that this probe tested subprocess of user input on other routes (health ignores extra query); that Burp 1048832 ran; that a command was run on the server.

**Helpers:** `casa_auth_qa/casa_519_probe.py`. Do **not** attach `/login`.

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.9/CASA_5_1_9_oscmd_page1.png`](tac_images/5.1.9/CASA_5_1_9_oscmd_page1.png) | Write-up |
| [`tac_images/5.1.9/CASA_5_1_9_oscmd_page2.png`](tac_images/5.1.9/CASA_5_1_9_oscmd_page2.png) | AL1 mapping |
| [`tac_images/5.1.9/CASA_5_1_9_oscmd_code.png`](tac_images/5.1.9/CASA_5_1_9_oscmd_code.png) | No subprocess |
| [`tac_images/5.1.9/CASA_5_1_9_oscmd_zap.png`](tac_images/5.1.9/CASA_5_1_9_oscmd_zap.png) | ZAP 90020 |
| [`tac_images/5.1.9/CASA_5_1_9_probe.png`](tac_images/5.1.9/CASA_5_1_9_probe.png) | Staging GET /health?q=$(id) → 200 JSON health, not command stdout |

### Portal comment

```
Official ADA ZAP scans did not report OS command injection or Shell Shock (ZAP 90020 FAIL, 10048 FAIL). The backend has no subprocess, os.system, or shell=True. Fluid SAST 5999aab9 was 0 High/Critical/Medium. Staging GET /api/v1/health with q=$(id) returned 200 JSON health (status ok); the body is not command stdout and the extra query is ignored. We did not run Burp 1048832. WSTG-INPV-12 is AL2 and was not run.
```

---

## 5.1.10 — File inclusion

**ADA:** AL1 DAST. Burp 1049344 / 1051392 shall not be identified.

**Claimed:** Auth path-traversal Highs are FP path segments (`team` / `templates` / `settings`). Ad click traversal is **404**, not `/etc/passwd`. Authenticated replay of all **4** plugin **6** URIs on staging (scan `33afa2aa`): **200** JSON team dashboard, **422** validation, **403** `mfa_required` on platform help settings. No local file contents.

**Missing:** Burp LFI plugins.

**Do not claim:** that Burp 1049344 / 1051392 ran; that 403 MFA reproduced a file-read; that production was scanned.

**Helpers:** `casa_auth_qa/casa_5110_replay.py` (`QA_PASSWORD`; local gitignored ZAP XML). Do **not** attach `/login`. Do **not** print the Bearer.

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.10/CASA_5_1_10_lfi_page1.png`](tac_images/5.1.10/CASA_5_1_10_lfi_page1.png) | Write-up |
| [`tac_images/5.1.10/CASA_5_1_10_lfi_page2.png`](tac_images/5.1.10/CASA_5_1_10_lfi_page2.png) | AL1 mapping |
| [`tac_images/5.1.10/CASA_5_1_10_lfi_code.png`](tac_images/5.1.10/CASA_5_1_10_lfi_code.png) | Object storage |
| [`tac_images/5.1.10/CASA_5_1_10_lfi_zap.png`](tac_images/5.1.10/CASA_5_1_10_lfi_zap.png) | Plugin 6 FP |
| [`tac_images/5.1.10/CASA_5_1_10_path.png`](tac_images/5.1.10/CASA_5_1_10_path.png) | Ad click traversal 404 |
| [`tac_images/5.1.10/CASA_5_1_10_auth_replay.png`](tac_images/5.1.10/CASA_5_1_10_auth_replay.png) | All 4 plugin 6 URIs replayed; no local file dump |

### Portal comment

```
Official SPA ZAP did not report directory listing or file inclusion as High. Auth ZAP 33afa2aa raised Path Traversal High/Low four times with empty evidence; the payloads were URL path segments such as team, templates, settings. Staging GET /ads/../etc/passwd/click is 404 JSON, not a local file. On 31 Aug 2026 we replayed all four plugin 6 URIs against api.stage.velvetelves.com with a staging Bearer (value not shown). GET /dashboard/team?view=team returned 200 JSON team health. POST /vendor-communications/templates returned 422 validation. PUT /platform/help/settings returned 403 mfa_required. None returned local file contents. Uploads go to object storage and are not executed. We did not run Burp 1049344 or 1051392.
```

---

## 5.2.1 — Malicious file uploads

**ADA:** AL1 written description plus source/screenshots of type checks and no execution.

**Claimed:** MIME allowlists; S3/Supabase storage; unsigned upload 401; authenticated disallowed MIME 415. Staging Compliance **Add document** picker lists PDF, DOC/DOCX, JPEG, PNG, WEBP, GIF, TXT, up to 20 MB (`CASA_5_2_1_picker.png`). No malware uploaded.

**Missing:** Malware sample (not attempted).

**Do not claim:** that a malware file was uploaded; that the picker is the only control (API 415 still applies).

**Helpers:** `casa_auth_qa/casa_521_picker.mjs` then `python casa_521_caption.py` (`QA_PASSWORD`). Do **not** attach `/login`. Do **not** upload malware.

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.2.1/CASA_5_2_1_uploads_page1.png`](tac_images/5.2.1/CASA_5_2_1_uploads_page1.png) | Write-up |
| [`tac_images/5.2.1/CASA_5_2_1_uploads_page2.png`](tac_images/5.2.1/CASA_5_2_1_uploads_page2.png) | AL1 mapping |
| [`tac_images/5.2.1/CASA_5_2_1_uploads_code.png`](tac_images/5.2.1/CASA_5_2_1_uploads_code.png) | MIME allowlists |
| [`tac_images/5.2.1/CASA_5_2_1_deny.png`](tac_images/5.2.1/CASA_5_2_1_deny.png) | Unsigned POST /documents/upload 401 |
| [`tac_images/5.2.1/CASA_5_2_1_415.png`](tac_images/5.2.1/CASA_5_2_1_415.png) | Authenticated probe.exe 415 |
| [`tac_images/5.2.1/CASA_5_2_1_picker.png`](tac_images/5.2.1/CASA_5_2_1_picker.png) | Staging Compliance picker allowlist (no file uploaded) |

### Portal comment

```
Deal documents POST /documents/upload allow PDF, DOCX, DOC, JPEG, PNG, WEBP, GIF, and TXT, max 20 MB; other types are 415. Logos allow JPEG, PNG, WEBP, SVG, GIF, max 2 MB. Files go to Supabase Storage / S3 and are not executed as HTML, JavaScript, or Python. Staging unsigned POST /documents/upload is 401. Authenticated upload of a tiny dummy probe.exe with Content-Type application/x-msdownload is 415. The staging Compliance Add document picker lists PDF, DOC/DOCX, JPEG, PNG, WEBP, GIF, TXT, up to 20 MB. We did not upload malware.
```

---

## 6.1.1 — No known exploitable components

**ADA:** AL1 dependency scan output. CVE CVSS >= 7.0 needs unused-code or no-patch justification.

**Claimed:** npm audit --omit=dev 0 vulns. pip-audit: only ecdsa 0.19.2 PYSEC-2026-1325 / CVE-2024-23342 CVSS 7.4; no upstream fix; JWT verify uses python-jose[cryptography], not ecdsa signing. Production ECR `velvet-elves/backend:prod-latest` is an OCI **image index** (Buildx); ECR cannot scan the index. The **linux/amd64** child Image (`sha256:96e074af…`) scan on 29 Aug 2026 was **Complete**: **48 Critical, 174 High**, 7 Medium, 1 Low. That scan is the OS/base layer (`python:3.12-slim`), not the application lockfile.

**Missing:** OWASP dependency-check; ECS task-definition digest confirmation (optional).

**Do not claim:** 0 High/Critical on the production image; that the image index was scanned; that all 48/174 image findings were triaged as unused; that we re-ran the scan on 31 Aug (the complete scan is 29 Aug, same prod-latest push).

### Images

| File | Description |
| --- | --- |
| [`tac_images/6.1.1/CASA_6_1_1_deps_page1.png`](tac_images/6.1.1/CASA_6_1_1_deps_page1.png) | Write-up |
| [`tac_images/6.1.1/CASA_6_1_1_deps_page2.png`](tac_images/6.1.1/CASA_6_1_1_deps_page2.png) | AL1 mapping |
| [`tac_images/6.1.1/CASA_6_1_1_deps_code.png`](tac_images/6.1.1/CASA_6_1_1_deps_code.png) | Pins |
| [`tac_images/6.1.1/CASA_6_1_1_pip.png`](tac_images/6.1.1/CASA_6_1_1_pip.png) | pip-audit ecdsa only |
| [`tac_images/6.1.1/CASA_6_1_1_npm.png`](tac_images/6.1.1/CASA_6_1_1_npm.png) | npm audit 0 vulns |
| [`tac_images/6.1.1/CASA_6_1_1_ecr.png`](tac_images/6.1.1/CASA_6_1_1_ecr.png) | ECR Complete scan of linux/amd64 child: 48 Critical, 174 High |
| [`tac_images/6.1.1/CASA_6_1_1_ecr_index.png`](tac_images/6.1.1/CASA_6_1_1_ecr_index.png) | prod-latest Image Index; Scan not found; points at amd64 child |

### Portal comment

```
Local pip-audit of backend requirements.txt on 31 Aug 2026 reported one finding: ecdsa 0.19.2 PYSEC-2026-1325 (CVE-2024-23342, CVSS 7.4). There is no upstream fix. Session JWTs are verified with python-jose[cryptography], not ecdsa.SigningKey.sign_digest (verification is out of scope for that CVE). npm audit --omit=dev on the SPA reported 0 vulnerabilities. Production ECR velvet-elves/backend:prod-latest is an OCI image index from Docker Buildx; Amazon ECR cannot scan that index (Scan not found / UnsupportedImageTypeException). The linux/amd64 child Image was scanned by Amazon ECR on 29 Aug 2026 (status Complete): 48 Critical, 174 High, 7 Medium, 1 Low. That result is the OS/base layer (python:3.12-slim), not the application lockfile. pydantic-ai-slim 1.107.5 and pypdf 6.16.2 are pinned in requirements.txt.
```

---

## 6.2.1 — Debug off in production

**ADA:** AL1 DAST. Burp 1050624 ASP.NET debugging.

**Claimed:** Prod `/api/docs` `/redoc` `/openapi.json` **404**. Staging docs **200**. ECS task `velvet-elves-prod-backend` revision **52**: `APP_DEBUG=false`, `APP_ENV=production` (plain env). Secrets are `valueFrom` Secrets Manager ARNs, not plaintext.

**Missing:** Burp 1050624 (N/A ASP.NET).

**Do not claim:** that Burp 1050624 ran; that secret **values** are shown (only ARNs).

### Images

| File | Description |
| --- | --- |
| [`tac_images/6.2.1/CASA_6_2_1_debug_page1.png`](tac_images/6.2.1/CASA_6_2_1_debug_page1.png) | Write-up |
| [`tac_images/6.2.1/CASA_6_2_1_debug_page2.png`](tac_images/6.2.1/CASA_6_2_1_debug_page2.png) | AL1 mapping |
| [`tac_images/6.2.1/CASA_6_2_1_debug_code.png`](tac_images/6.2.1/CASA_6_2_1_debug_code.png) | docs off in prod |
| [`tac_images/6.2.1/CASA_6_2_1_debug_zap.png`](tac_images/6.2.1/CASA_6_2_1_debug_zap.png) | ZAP 10023 |
| [`tac_images/6.2.1/CASA_6_2_1_docs.png`](tac_images/6.2.1/CASA_6_2_1_docs.png) | Prod 404 / staging 200 |
| [`tac_images/6.2.1/CASA_6_2_1_ecs_env.png`](tac_images/6.2.1/CASA_6_2_1_ecs_env.png) | Prod task rev 52: APP_DEBUG=false, APP_ENV=production |

### Portal comment

```
Production FastAPI hides OpenAPI UI: GET https://api.prod.velvetelves.com/api/docs, /api/redoc, and /api/openapi.json are 404. Staging still serves /api/docs (200). ECS task definition velvet-elves-prod-backend revision 52 sets APP_DEBUG=false and APP_ENV=production as plain environment values. API keys and APP_SECRET_KEY are valueFrom AWS Secrets Manager ARNs, not plaintext in the task. Official ZAP listed generic JSON 500 application-error as Low, not a debug console. We did not run Burp 1050624 (ASP.NET debugging); this app is FastAPI.
```

---

## 6.3.1 — Origin not used for authz

**ADA:** AL1 DAST. Burp 2098689 arbitrary origin trusted.

**Claimed:** JWT authz. Foreign Origin GET /users/me is 401. CORS allowlist (3.1.5).

**Missing:** Burp 2098689.

### Images

| File | Description |
| --- | --- |
| [`tac_images/6.3.1/CASA_6_3_1_origin_page1.png`](tac_images/6.3.1/CASA_6_3_1_origin_page1.png) | Write-up |
| [`tac_images/6.3.1/CASA_6_3_1_origin_page2.png`](tac_images/6.3.1/CASA_6_3_1_origin_page2.png) | AL1 mapping |
| [`tac_images/6.3.1/CASA_6_3_1_origin_code.png`](tac_images/6.3.1/CASA_6_3_1_origin_code.png) | JWT not Origin |
| [`tac_images/6.3.1/CASA_6_3_1_origin_zap.png`](tac_images/6.3.1/CASA_6_3_1_origin_zap.png) | ZAP 10098/20016 |
| [`tac_images/6.3.1/CASA_6_3_1_origin.png`](tac_images/6.3.1/CASA_6_3_1_origin.png) | Origin evil 401 |

### Portal comment

```
Access control is the JWT plus require_role / require_tenant_access. The Origin header is not used to grant a session. Staging GET /users/me with Origin https://evil.example and no Bearer is 401. CORS allowlists SPA origins (a foreign Origin does not receive Access-Control-Allow-Origin). Official ZAP 10098/20016 are WARN. We did not run Burp 2098689.
```

---

## 6.4.1 — Subdomain takeover

**ADA:** AL1 DNS evidence that names point at resources you control.

**Claimed:** Live DNS for app/api/help/apex to CloudFront or ALB. Route 53 hosted zone `velvetelves.com`: `app` / `app.stage` / `help` / `help.stage` alias to CloudFront; `api.prod` alias to prod API ALB; `api.stage` CNAME to stage API ALB. Underscore CNAMEs are ACM DNS validation (Amazon), not abandoned SaaS.

**Missing:** Full dangling-CNAME audit of all unused names in the 46-record zone. Zone apex row is not in this filtered console shot (live DNS PNG already covers `velvetelves.com`).

**Do not claim:** that this PNG shows the zone apex record; that every one of the 46 records was reviewed; that zone id `Z04016973TWW2D0EKIMFB` is visible in the frame.

### Images

| File | Description |
| --- | --- |
| [`tac_images/6.4.1/CASA_6_4_1_dns_page1.png`](tac_images/6.4.1/CASA_6_4_1_dns_page1.png) | Write-up |
| [`tac_images/6.4.1/CASA_6_4_1_dns_page2.png`](tac_images/6.4.1/CASA_6_4_1_dns_page2.png) | AL1 mapping |
| [`tac_images/6.4.1/CASA_6_4_1_dns_code.png`](tac_images/6.4.1/CASA_6_4_1_dns_code.png) | Name list |
| [`tac_images/6.4.1/CASA_6_4_1_dns.png`](tac_images/6.4.1/CASA_6_4_1_dns.png) | Live A/AAAA answers |
| [`tac_images/6.4.1/CASA_6_4_1_route53.png`](tac_images/6.4.1/CASA_6_4_1_route53.png) | Route 53 app/api/help → CloudFront or ALB |

### Portal comment

```
Live DNS on 31 Aug 2026: app.velvetelves.com and app.stage.velvetelves.com resolve to CloudFront addresses; api.prod.velvetelves.com and api.stage.velvetelves.com resolve to ALB addresses; help.velvetelves.com and velvetelves.com resolve. Route 53 hosted zone velvetelves.com shows app, app.stage, help, and help.stage as alias A/AAAA to CloudFront; api.prod as alias A to the prod API ALB; api.stage as CNAME to the stage API ALB. Underscore CNAMEs are ACM certificate validation at Amazon, not abandoned Heroku, GitHub, or S3 website endpoints. This filtered view does not include the zone apex row. WSTG-CONF-10 is AL2 and was not run.
```

---

## 6.5.1 — Do not log credentials or payment details

**ADA:** Written description PLUS a login log sample PLUS a payment log sample.

**Claimed:** Code does not log passwords; emails masked; Stripe holds PAN.

**Missing (ADA-named):** CloudWatch (or other sink) sample from a real login. Sample from a real payment. These were NOT obtained.

### Images

| File | Description |
| --- | --- |
| [`tac_images/6.5.1/CASA_6_5_1_logs_page1.png`](tac_images/6.5.1/CASA_6_5_1_logs_page1.png) | Write-up; states log samples missing |
| [`tac_images/6.5.1/CASA_6_5_1_logs_page2.png`](tac_images/6.5.1/CASA_6_5_1_logs_page2.png) | AL1 mapping |
| [`tac_images/6.5.1/CASA_6_5_1_logs_code.png`](tac_images/6.5.1/CASA_6_5_1_logs_code.png) | _mask_email |
| [`tac_images/6.5.1/CASA_6_5_1_mask.png`](tac_images/6.5.1/CASA_6_5_1_mask.png) | Mask helper only, not CloudWatch |

### Portal comment

```
Login passwords are not written to the application logger. Gmail paths mask emails (local-part prefix plus ***). JSON logs include a request id, not the Authorization header. Card data is collected on Stripe Checkout; we store Stripe ids, not PAN or CVV. A CloudWatch (or other sink) extract captured during a live login was not obtained. A payment-process log extract was not obtained.
```

---

## 6.6.1 — Clear browser storage on logout

**ADA:** AL1 written description of what remains in the browser after logout.

**Claimed:** clearTokens removes velvet_elves_token and velvet_elves_refresh_token; POST /users/logout revokes. Staging 31 Aug 2026: both token keys present before Log Out, both absent after. UI is staging /login.

**Missing:** Chrome DevTools Application panel (Playwright evaluate used instead). velvet_elves_return_location remains after logout (path key, not a token).

### Images

| File | Description |
| --- | --- |
| [`tac_images/6.6.1/CASA_6_6_1_logout_page1.png`](tac_images/6.6.1/CASA_6_6_1_logout_page1.png) | Write-up |
| [`tac_images/6.6.1/CASA_6_6_1_logout_page2.png`](tac_images/6.6.1/CASA_6_6_1_logout_page2.png) | AL1 mapping |
| [`tac_images/6.6.1/CASA_6_6_1_logout_code.png`](tac_images/6.6.1/CASA_6_6_1_logout_code.png) | clearTokens |
| [`tac_images/6.6.1/CASA_6_6_1_after_logout.png`](tac_images/6.6.1/CASA_6_6_1_after_logout.png) | Staging /login after Log Out (this session) |
| [`tac_images/6.6.1/CASA_6_6_1_storage.png`](tac_images/6.6.1/CASA_6_6_1_storage.png) | Token keys present then absent; return_location remains |

### Portal comment

```
The SPA stores velvet_elves_token and velvet_elves_refresh_token in localStorage. Logout calls POST /users/logout (revokes the Supabase session) then clearTokens(), which removes both keys. Staging after Log Out: those two keys are gone; velvet_elves_return_location remains; the browser is on /login. Google tokens are not in the browser. A Chrome DevTools Application panel was not captured (Playwright evaluate of key presence only; values not shown).
```

---

## 6.7.1 — Server-side secrets

**ADA:** Written description plus source/screenshots of secrets management.

**Claimed:** Secrets Manager for ENCRYPTION_KEY; Fernet for Google tokens; production fail-closed; Disconnect soft-deactivate.

**Missing:** AWS Secrets Manager console screenshot; CloudTrail secret-access log screenshot. No secret values attached (correct).

### Images

| File | Description |
| --- | --- |
| [`tac_images/6.7.1/CASA_6_7_1_secrets_page1.png`](tac_images/6.7.1/CASA_6_7_1_secrets_page1.png) | Write-up |
| [`tac_images/6.7.1/CASA_6_7_1_secrets_page2.png`](tac_images/6.7.1/CASA_6_7_1_secrets_page2.png) | AL1 mapping |
| [`tac_images/6.7.1/CASA_6_7_1_secrets_code.png`](tac_images/6.7.1/CASA_6_7_1_secrets_code.png) | No secret values |

### Portal comment

```
API secrets including ENCRYPTION_KEY live in AWS Secrets Manager, not in git. Production fails to start if ENCRYPTION_KEY is missing. Google access and refresh tokens are Fernet-encrypted in the integrations table. Disconnect sets is_active false; ciphertext remains on the row (soft deactivate, not a wipe). The SPA does not hold those secrets. An AWS Secrets Manager console screenshot and a CloudTrail access-log screenshot were not taken. No secret values are attached.
```

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
| 3.1.1 | `python render_casa_311_pages.py` then `python casa_311_deny.py`. Do **not** attach `/login`. Do **not** query another tenant. |
| 3.1.2 | `python render_casa_312_pages.py` then `python casa_312_ignore.py`. Do **not** attach `/login`. Do **not** register a staging user to prove tenant_id ignore. |
| 3.1.3 | `python render_casa_313_pages.py` then `python casa_313_fail.py`. Do **not** attach `/login`. Do **not** call the tick with a valid secret. |
| 3.1.4 | `python render_casa_314_pages.py` then `python casa_314_deny.py`. Do **not** attach `/login`. Do **not** register a staging user. Do **not** query another tenant. |
| 3.1.5 | `python render_casa_315_pages.py` then `python casa_315_cors.py`. Do **not** attach `/login`. Do **not** recapture ZAP UI. Do **not** mint staging users for a fresh 429. |
| 3.1.6 | `python render_casa_316_pages.py` then `python casa_316_list.py`. Do **not** attach `/login`. Do **not** recapture ZAP UI or the AWS console. |
| 3.2.1 | `python render_casa_321_pages.py` then `python casa_321_pkce.py`. Do **not** attach `/login`. Do **not** recapture Google Cloud Console. Do **not** complete OAuth. |
| 3.2.2 | `python render_casa_322_pages.py` then `python casa_322_deny.py`. Do **not** attach `/login`. Do **not** recapture Google Cloud Console. Do **not** complete OAuth. |
| 3.3.1 | `python render_casa_331_pages.py` then `python casa_331_deny.py`. Prod UI: `node casa_331_prod_enroll_shots.mjs` (`QA_PASSWORD`). Folder is the upload set only. |
| 4.1.1 | `python render_casa_411_pages.py` then `python casa_411_tls.py`. SSL Labs: `node casa_411_ssllabs.mjs app` then `node casa_411_ssllabs.mjs api`, then `python casa_411_caption_ssllabs.py` once. |
| 4.1.2 | `python render_casa_412_pages.py` then `python casa_412_certs.py` (copies Qualys PNGs from 4.1.1; do not recapture ssllabs.com or the ACM console). |
| 4.1.3 | `python render_casa_413_pages.py` then `python casa_413_fernet.py`. Do **not** print or attach ENCRYPTION_KEY. |
| 4.1.4 | `python render_casa_414_pages.py` then `python casa_414_fail.py`. Do **not** print ENCRYPTION_KEY or JWTs. |
| 5.1.1 | `python render_casa_511_pages.py` then `python casa_511_hpp.py`. Do **not** attach `/login`. Do **not** recapture ZAP UI. |
| 5.1.2 | `python render_casa_512_pages.py` then `python casa_512_deny.py`. Do **not** attach `/login`. Do **not** recapture ZAP UI or Google Cloud Console. Do **not** complete OAuth. |
| 5.1.3–6.7.1 | `python render_casa_rest.py` then `python casa_rest_live.py`. 5.1.4 extra: `python casa_514_probe.py`. 5.1.7 extra: `node casa_517_stored.mjs` then `python casa_517_caption.py` (`QA_PASSWORD`; deletes the contact). 5.1.8 extra: `python casa_518_replay.py` (`QA_PASSWORD`; local gitignored ZAP XML). 5.1.9 extra: `python casa_519_probe.py`. 5.1.10 extra: `python casa_5110_replay.py` (`QA_PASSWORD`; local gitignored ZAP XML). 5.2.1 extra: `node casa_521_picker.mjs` then `python casa_521_caption.py` (`QA_PASSWORD`; no file uploaded). Auth extras: `python casa_rest_auth_extra.py` then `node casa_661_storage.mjs` then `python casa_661_render.py` (`QA_PASSWORD`). Do **not** recapture ZAP, Burp, AWS, or CloudWatch. Do **not** print secrets. |

Eyeball every PNG for cut-off text before re-upload.
