# CASA AL1 — portal pack (comments and image descriptions)

**Filename (fixed):** `casa_al1_evidence/m9/CASA_PORTAL_PACK.md` — do not rename. Append new rows here; update the scope line only.  
**Updated:** 28 Aug 2026  
**Rows in this file:** 1.1.1, 1.1.2, 1.1.3, 1.2.1  
**Portal:** https://casa.tacsecurity.com/ — per-row **Upload Evidences** (PNG/JPG/JPEG, max 10). Do not upload this markdown.  
**Images:** `casa_al1_evidence/m9/tac_images/<check-id>/` — one folder per row. MFA shots for later row 3.3.1 are in `tac_images/3.3.1/` (do not attach those on 1.1.x / 1.2.1).  
**Operating guide:** `CASA/TAC_ESOF_PORTAL_GUIDE.md` §7  
**ADA source:** [Web App Test Guide v1.0](https://github.com/appdefensealliance/ASA-WG/blob/v1.0/Web%20App%20Profile/Web%20App%20Test%20Guide.md)

Do not check “I confirm…” or click Evidence **Submit** until all 48 rows are filled.

**Screenshot rule:** agent captures Velvet Elves only (`app.` / `api.` staging or production, plus our own write-up PNGs). Screenshots of other products (Supabase dashboard, supabase.com docs, SSL Labs, AWS, Google Cloud) are owner-captured. If one is needed, the agent will ask and give guidelines — it will not take the shot.

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

## Regeneration

From `casa_auth_qa/` (headless Chrome; one page at a time):

| Row | Commands |
| --- | --- |
| 1.1.1 | `python render_casa_111_pages.py` then live/UI shot scripts |
| 1.1.2 | `python render_casa_112_pages.py` then `node casa_112_shots.mjs` |
| 1.1.3 | `python render_casa_113_pages.py` only. Do **not** recapture supabase.com. |
| 1.2.1 | `python render_casa_121_pages.py` then `node casa_121_shots.mjs` (Velvet Elves staging only). |

Eyeball every PNG for cut-off text before re-upload.
