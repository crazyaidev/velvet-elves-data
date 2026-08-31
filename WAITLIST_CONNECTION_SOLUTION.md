# Waitlist Connection for Okos — Solution

**Date:** 2026-08-25  
**Status:** **Implemented** on production project `kbgvnsjdkgzixpeazmtn` (2026-08-25)  
**Reviewed:** 2026-08-25 — workflow/logic review against as-built code and `velvet-elves-data`  
**Request:** Jake, email “Waitlist Connection”  
**Repos checked:** `velvet-elves-backend`, `velvet-elves-frontend`, `velvet-elves-marketing-website`, `velvet-elves-data`

DSN (password included) is in gitignored `velvet-elves-backend/.env.okos-waitlist-ro`. Share via a password-manager one-time link. Do not commit, email, or WhatsApp it.

---

## 0. What this review changed

The previous draft’s **goal** (read-only, no product credentials, Session pooler, stay off the VM) was right. Several **workflow and Postgres logic** choices were wrong. Those are corrected below. Source code is unchanged.

| Flaw in the previous draft | Why it is wrong | Correction |
|----------------------------|-----------------|------------|
| Primary path is a view named `marketing_waitlist_export` | Jake’s enable step is “paste the Session pooler DSN into `waitlist-dsn.txt` and flip enabled.” His own SQL reads `public.marketing_leads`. A renamed relation is an Okos code/config change, not a DSN-only enable. | **Primary path keeps `public.marketing_leads`.** Tighten his script: `USING (interest = 'waitlist')` instead of `USING (true)`. |
| “Do not add an RLS policy” as a design goal | `marketing_leads` has RLS enabled and **no** policies (`20260902090000`). A LOGIN role that SELECTs that table **must** have a policy or it sees **zero rows** (Jake’s verify note). A role-scoped policy does **not** change capture: the API uses the service role, which bypasses RLS (`SYSTEM_DESIGN.md` §1.3; `get_supabase`). | Policy is the correct mechanism. Reject only `USING (true)`, not policies as such. |
| §8 column-level `GRANT SELECT (…)` omitting `user_agent` | In Postgres, `SELECT *` expands to every column and **fails** if any column lacks `SELECT`. We do not know Okos’s SQL. Column grants can make “flip enabled” fail. | Full-table `GRANT SELECT`. `user_agent` stays on the row (bot-triage; the SPA omits it, the DB does not). |
| No `DROP POLICY` if Jake already ran his script | Permissive policies for the same role **OR** together. `USING (true)` OR `USING (interest = 'waitlist')` = all four lists. | Always `DROP POLICY IF EXISTS okos_waitlist_ro_read` (and any other policy for that role on this table) before creating the waitlist-only policy. |
| `CONNECTION LIMIT 5` on first enable | Unknown Okos pool size. A pool of 6+ fails with a role connection error **after** he flips enabled. | Do **not** set a limit until the first pull succeeds. Harden afterward if needed. |
| View described as inherently read-only | Simple single-table views are **auto-updatable**. Writes are blocked today only because we do not `GRANT INSERT/UPDATE/DELETE`. | Explicit `REVOKE` of writes on the table. Optional view (appendix) must stay `security_invoker = false` and must not be treated as a substitute for revoke. |
| Conflated `USING (true)` with `user_agent` leak | `USING (true)` leaks **rows** (newsletter / demo / early_access). `user_agent` is a **column** issue. | Filter rows with `interest = 'waitlist'`. Do not pretend that hides `user_agent`. |
| “Same columns as `GET /api/v1/platform/marketing-leads`” | That JSON is `{ items, total, counts }`. Item fields include `id`. The CSV omits `id` and `user_agent` (`PlatformWaitlistPage.tsx` `toCsv`). | Say **item** shape vs CSV vs raw table clearly. |
| §9 `Authorization: Bearer <machine-key>` as if it works today | `list_marketing_leads` is `Depends(require_platform_admin)` → `get_current_user` → **Supabase user JWT**. A random bearer or CRM `X-API-Key` returns **401**. CRM keys are tenant-scoped inbound contacts, not platform marketing. | HTTP machine key is **future work**. Do not try it for this email. |
| R3 “do not change the marketing app” vs “query a different relation” | R3 means Jan does not SSH or edit Okos. Requiring a new table name still forces Jake to change Okos before enable. | Primary SQL matches the relation in his email. |

---

## 1. Verdict

Jake’s **goal is correct.** Okos on Lightsail needs a read-only pull of launch-waitlist signups, it must not use the `postgres` user or the service role, and the host must be the **Session pooler** (direct `db.kbgvnsjdkgzixpeazmtn.supabase.co` is IPv6-only; Lightsail is IPv4). That matches backend `.env.example` (pooler on `:5432`; direct marked IPv6).

His **script is the right shape** (dedicated `LOGIN`, `CONNECT`, `USAGE`, `SELECT`, plus a policy because RLS is on). It is **not** shippable as written because `USING (true)` exposes all four `interest` values. Product rule: those lists are different promises (`MARKETING_WAITLIST_IMPLEMENTATION_PLAN.md` D1; `app/schemas/marketing.py`). The in-app console defaults to Waitlist for the same reason (`PlatformWaitlistPage.tsx`).

**Ship:** his role and DSN workflow, with `USING (interest = 'waitlist')`, write privileges revoked, his `USING (true)` policy dropped if it exists, password not sent on WhatsApp.

Do **not** put a platform-admin user JWT on the VM. `require_platform_admin` is the vendor superuser gate (`app/core/auth.py`): tenants, users, billing, Help Center CMS, advertising — not waitlist-only.

---

## 2. Requirements (this email, mapped)

| # | What he asked | Keep? |
|---|----------------|-------|
| R1 | Okos reads waitlist data without Jan’s product credentials | Yes |
| R2 | Read-only; cannot break capture or hello@ | Yes |
| R3 | Jan does not log into `/opt/okos` or edit Okos | Yes |
| R4 | IPv4 / Session pooler URI; two substitutions (user, password) | Yes |
| R5 | He pastes DSN into `waitlist-dsn.txt` and flips enabled | Yes — **same relation `public.marketing_leads`** |
| R6 | Password via WhatsApp | **No** — same secret, password-manager one-time link (§7) |

R6 is the only letter-of-the-request refusal. Capture, `/platform/waitlist`, and velvetelves.com are out of scope for change.

Human path until Okos is live: `/platform/waitlist` CSV (filter defaults to Waitlist; export is the filtered rows, not the whole table). That is waitlist plan R6 already shipped (`requirements.txt` §16.4).

---

## 3. As-built (the pipe Okos is attaching to)

### 3.1 No separate waitlist database

The marketing site’s own Supabase project is gone.

- `20260902090000_marketing_leads.sql`: platform-global, no `tenant_id`; RLS on; **no anon policy**; service role mediates writes.
- Marketing site `src/lib/api.ts`: only DB write on the site is `POST /api/v1/public/marketing/leads`.
- `app/api/v1/router.py`: unified into this backend; no separate DB.

Production ref (Jake’s host): `kbgvnsjdkgzixpeazmtn`.

### 3.2 Four lists, one table

`interest` ∈ `waitlist | demo_waitlist | newsletter | early_access` (`20260920090000_marketing_waitlist.sql`). Unique key `(lower(email), interest)` — the same address can sit on more than one list. `GROUP BY interest` counts **rows**, not people.

| `interest` | Promise | Okos waitlist mail? |
|------------|---------|---------------------|
| `waitlist` | Founding pricing + demo | **Yes** |
| `demo_waitlist` | Notify when the demo is ready | No |
| `newsletter` | Footer subscribe | No |
| `early_access` | Roles that cannot self-sign-up | No |

Raw table columns: `id`, `email` (plaintext, lowercased), `source_page`, `interest`, `user_agent`, `referrer`, `created_at`, `confirmation_email_sent_at`. Emails on this table are **not** Fernet-encrypted (`SYSTEM_DESIGN.md` Fernet applies to repository PII / integration tokens, not `marketing_leads`).

Platform **item** JSON (`PlatformMarketingLeadItem`): those columns except `user_agent`. Platform **CSV**: no `id`, no `user_agent`.

### 3.3 Capture path (must stay untouched)

`POST /api/v1/public/marketing/leads` (`public_marketing.py`), service-role client:

- honeypot `company` → 200, no row
- 10 req / min / IP
- existing `(email, interest)` → 200, no second row
- hello@ only for a **new** `interest = 'waitlist'` row (`marketing_waitlist_email.py`; claim on `confirmation_email_sent_at`)

A `SELECT`-only role cannot insert, update, claim, or suppress that mail **if it has no write grants**. A policy `TO okos_waitlist_ro` does not apply to `service_role` or to `anon` (no matching policy, no table GRANT in the migration).

### 3.4 Existing HTTP read is the wrong credential for this VM

| Surface | Auth today | Notes |
|---------|------------|--------|
| `GET /api/v1/platform/marketing-leads` | Supabase **user** JWT + `is_platform_admin` | Default `limit` 100, max 1000; `interest` query optional |
| `/platform/waitlist` | Same, in the SPA | Default segment Waitlist |

`test_platform_marketing_api.py`: anonymous 401/403; non-admin **403**. Tenant CRM `X-API-Key` (`crm_sync.py` / `tenant_api_keys`) authenticates **inbound contacts**, not this GET. There is **no** platform marketing machine key today.

---

## 4. Postgres rules this plan depends on

1. **RLS default deny.** Role is not table owner and has no `BYPASSRLS`. `GRANT SELECT` without a matching policy → **empty result**, not an error. Jake’s “if it prints nothing, the policy didn’t take” is correct for table SELECT.
2. **Permissive policies OR.** Two `FOR SELECT TO okos_waitlist_ro` policies combine with OR. A leftover `USING (true)` nullifies a later waitlist-only policy. **Drop the old one.**
3. **Service role bypasses RLS.** Capture and `/platform/waitlist` stay on `get_supabase()` (service role). This LOGIN does not share that path.
4. **`SELECT *` needs every column.** Do not use column-level GRANT unless Okos’s SELECT list is known.
5. **PUBLIC grants still apply** to a new LOGIN (you cannot peel them off without revoking FROM PUBLIC). Isolation is “no extra table GRANTs,” not “this role is a sealed sandbox.” After create, inspect `information_schema.table_privileges` for `okos_waitlist_ro` and `PUBLIC` on `public` tables.

---

## 5. Specific solution (run this)

**Where:** production SQL editor, project `kbgvnsjdkgzixpeazmtn` only. Not staging, not a git migration (password must not hit the repo). Do not SSH to Lightsail. Do not change application source.

```
Okos VM (IPv4)
  → Session pooler (IPv4, :5432)
    → LOGIN okos_waitlist_ro
      → SELECT public.marketing_leads
         RLS: interest = 'waitlist' only
```

Write path unchanged:

```
velvetelves.com → POST /api/v1/public/marketing/leads → service role → marketing_leads
```

Console unchanged:

```
/platform/waitlist → GET /api/v1/platform/marketing-leads → service role
```

### 5.1 Password

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Store in the team password manager **before** the SQL editor. Do not paste into chat, email, or WhatsApp.

### 5.2 SQL (production editor)

Replace only the password placeholder. Run **each statement with autocommit** (or as separate SQL-editor statements). Do **not** wrap `CREATE ROLE` in a `DO $$` transaction — Postgres rejects that.

On hosted Supabase, `postgres` is **not** a real superuser. `ALTER ROLE … NOSUPERUSER` fails with *permission denied to alter role* even when the role is already non-superuser. Put the flags on `CREATE ROLE`; afterward only `ALTER ROLE … PASSWORD`.

```sql
-- 1) If his USING (true) policy was already created, drop it.
--    Permissive policies OR together; leaving it would leak all interests.
DROP POLICY IF EXISTS okos_waitlist_ro_read ON public.marketing_leads;
DROP POLICY IF EXISTS okos_waitlist_ro_waitlist_only ON public.marketing_leads;

-- 2) Role: login, not superuser, does not bypass RLS.
--    Skip CREATE if the role already exists; then only ALTER PASSWORD.
CREATE ROLE okos_waitlist_ro
    LOGIN
    PASSWORD 'PUT-THE-GENERATED-PASSWORD-HERE'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOBYPASSRLS;

-- If the role already exists (password rotate):
-- ALTER ROLE okos_waitlist_ro PASSWORD 'PUT-THE-GENERATED-PASSWORD-HERE';

GRANT CONNECT ON DATABASE postgres TO okos_waitlist_ro;
GRANT USAGE ON SCHEMA public TO okos_waitlist_ro;

-- 3) Table: SELECT only. Full column list so SELECT * still works.
REVOKE ALL ON TABLE public.marketing_leads FROM okos_waitlist_ro;
GRANT SELECT ON TABLE public.marketing_leads TO okos_waitlist_ro;

-- 4) Row filter: launch waitlist only. Does not apply to service_role / postgres.
CREATE POLICY okos_waitlist_ro_waitlist_only
    ON public.marketing_leads
    FOR SELECT
    TO okos_waitlist_ro
    USING (interest = 'waitlist');
```

Do **not** `GRANT` this table (or a view over it) to `anon` or `authenticated`. Do **not** add the role to `service_role`.

Do **not** set `CONNECTION LIMIT` until Okos has pulled once. Then, if you cap it, tell Jake the number so his pool stays below it.

### 5.3 Verify (same editor, as `postgres` then `SET ROLE`)

```sql
-- Hygiene: this role must not have SELECT on other public tables.
SELECT table_schema, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'okos_waitlist_ro'
ORDER BY 1, 2, 3;

SET ROLE okos_waitlist_ro;

-- Success = only interest waitlist. Empty = policy/GRANT failed,
-- OR there are zero waitlist rows (check as postgres before assuming failure).
-- Newsletter/demo/early_access MUST NOT appear — that is success, not a broken policy.
SELECT interest, COUNT(*) FROM public.marketing_leads GROUP BY interest;

RESET ROLE;

-- Confirm leftover USING (true) is gone.
SELECT pol.polname, pg_get_expr(pol.polqual, pol.polrelid) AS using_expr
FROM pg_policy pol
JOIN pg_class c ON c.oid = pol.polrelid
WHERE c.relname = 'marketing_leads';
```

If `SET ROLE` is not allowed in the dashboard session, run the `GROUP BY` from a Session-pooler connection as `okos_waitlist_ro` after §5.4 (that is the real consumer path anyway).

### 5.4 Connection string (his procedure)

1. Dashboard → **Connect** → **Session pooler** URI (not Direct; not transaction pooler `:6543`).
2. Username `postgres.kbgvnsjdkgzixpeazmtn` → `okos_waitlist_ro.kbgvnsjdkgzixpeazmtn`.
3. Password → the generated one.
4. Host and port unchanged.

He pastes into `/opt/okos/data/secrets/ve/waitlist-dsn.txt` and enables. Jan does not write that file.

Tell him in the secret note:

- Query `public.marketing_leads` as he already planned.
- RLS returns **`waitlist` rows only**. His sample “waitlist 1 and newsletter 1” was a **full-table** snapshot from the session connector. After this role, **newsletter must not appear**.
- `user_agent` is still on the row if he `SELECT *`.

---

## 6. What this does not change

- Application source, git migrations, staging.
- velvetelves.com capture, honeypot, rate limit, idempotency, hello@.
- `/platform/waitlist` and `GET /api/v1/platform/marketing-leads`.
- `postgres` password, service role, anon key.

---

## 7. Secret handling

| Do | Do not |
|----|--------|
| `secrets.token_urlsafe(32)` | Short / reused password |
| Password manager, then a **one-time view link** | WhatsApp, SMS, this email thread |
| He copies into `waitlist-dsn.txt` | Jan SSH / scp onto Lightsail |
| Rotate with `ALTER ROLE okos_waitlist_ro PASSWORD '…'` | Leave the password sitting in the SQL editor tab |

CASA: new production LOGIN. Data: **plaintext waitlist emails** (and `user_agent` if `SELECT *`). Path: Lightsail Okos → Session pooler → `marketing_leads` under `okos_waitlist_ro` RLS. It is **not** access to deals, users, or integration tokens. Record that data flow in the assessment.

---

## 8. Optional later: export view (only if Okos can change the relation)

Use this **after** enable, and only if he can point Okos at another relation. It hides `user_agent` and keeps the LOGIN off the base table name in his SQL.

It is **not** the primary path: it breaks DSN-only enable if Okos is hardcoded to `public.marketing_leads`.

```sql
CREATE OR REPLACE VIEW public.marketing_waitlist_export
WITH (security_invoker = false) AS
SELECT
    id,
    email,
    source_page,
    interest,
    referrer,
    created_at,
    confirmation_email_sent_at
FROM public.marketing_leads
WHERE interest = 'waitlist'
OFFSET 0;  -- not auto-updatable

-- Default view uses the owner's rights (postgres bypasses RLS).
-- security_invoker = true would apply THIS role's RLS and need GRANT on the
-- base table; an invoker view with no table policy returns zero rows.

GRANT SELECT ON public.marketing_waitlist_export TO okos_waitlist_ro;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER
    ON public.marketing_waitlist_export FROM okos_waitlist_ro;
```

Do not `GRANT` the view to `anon` / `authenticated` (PostgREST exposes `public`). Then `REVOKE SELECT` on the base table from `okos_waitlist_ro` and drop `okos_waitlist_ro_waitlist_only` only after Okos is confirmed on the view.

**Do not** use column-level `GRANT` on `marketing_leads` as a way to hide `user_agent` unless Okos’s SELECT list is known not to be `SELECT *`.

---

## 9. Later (not this email): HTTP machine key

When Okos can call HTTPS, retire the LOGIN.

That requires **new** application work: a platform-scoped key (hash at rest, shown once, revocable — like `tenant_api_keys`) allowed **only** on `GET /api/v1/platform/marketing-leads?interest=waitlist`. Today that route will **401** anything that is not a platform-admin user JWT.

Production API host (as-built): `https://api.prod.velvetelves.com`. Client pagination already walks `limit=1000` (`useFetchAllMarketingLeads.ts`).

After that ships: `REVOKE CONNECT` from `okos_waitlist_ro`, drop the policy (and view if any).

---

## 10. Execution checklist

1. ~~Generate password; store in password manager.~~ Done (`secrets.token_urlsafe(32)`). DSN in gitignored `.env.okos-waitlist-ro`.
2. ~~Production: run §5.2.~~ Done 2026-08-25 via session pooler as `postgres`.
3. ~~Run §5.3.~~ Verified (see §12).
4. ~~Copy Session pooler URI; two substitutions (§5.4).~~ Done (same host/port as `PROD_SUPABASE_DB_URL`, user `okos_waitlist_ro.kbgvnsjdkgzixpeazmtn`).
5. Share DSN + the three bullets in §5.4 via one-time secret link (**not** WhatsApp).
6. Jake pastes `waitlist-dsn.txt` and enables. Confirm a pull of **waitlist** rows only.
7. Optional: set `CONNECTION LIMIT` to something above his observed pool; tell him the cap.
8. Record the CASA data flow (§7).
9. Optional later: §8 view or §9 HTTP key.

---

## 11. Suggested reply (facts only)

- The read-only Session-pooler role is in. I did not touch the VM or velvetelves.com.
- Same table he named: `public.marketing_leads`. He pastes the DSN and enables.
- Policy is `USING (interest = 'waitlist')`, not `USING (true)`. `GROUP BY interest` as this role will not show newsletter; that is intended (we confirmed waitlist-only vs a full-table newsletter+waitlist snapshot).
- Password / DSN via password-manager one-time link, not WhatsApp.
- `/platform/waitlist` still works; this DSN does not replace it.
- Security assessment: this LOGIN is waitlist rows in `marketing_leads` only, not the product database as a whole.

---

## 12. Production apply (2026-08-25)

Ran against the production Session pooler as `postgres` (port 5432). No application source change. No git migration. Password is **not** in this file.

| Check | Result |
|-------|--------|
| Role | `okos_waitlist_ro`: LOGIN, not superuser, not CREATEROLE/CREATEDB, NOINHERIT, no BYPASSRLS, `CONNECTION LIMIT` unlimited (`-1`) |
| Table grants to the role | `SELECT` on `public.marketing_leads` only |
| Policy | `okos_waitlist_ro_waitlist_only` → `(interest = 'waitlist'::text)` |
| Full table as `postgres` | `newsletter=1`, `waitlist=1` |
| Same `GROUP BY` as `okos_waitlist_ro` | `waitlist=1` only |
| `SELECT` on `public.users` | no privilege |
| `INSERT` into `marketing_leads` as the role | denied, SQLSTATE `42501` |
| DSN file | `velvet-elves-backend/.env.okos-waitlist-ro` (gitignored by `.env.*`) |

Hosted-Supabase notes (do not repeat the failed forms):

- `CREATE ROLE` must not run inside a transaction / `DO $$` block.
- `ALTER ROLE … NOSUPERUSER` is rejected because dashboard `postgres` is not SUPERUSER. Flags belong on `CREATE ROLE`; rotate with `ALTER ROLE … PASSWORD` only.

