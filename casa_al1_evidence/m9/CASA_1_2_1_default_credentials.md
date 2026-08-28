# CASA 1.2.1 — Default credentials shall not be present on publicly exposed interfaces

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 2.5.4  
**Date:** 28 Aug 2026  
**Do not claim:** ADA-approved IdP for Supabase; that we tested every possible default pair in the wild; that internal QA operator accounts are absent (they are operator-created, not shipped defaults).

## ADA definition

Default credentials are predefined username **and** password combinations (example: Admin/Admin). An admin account with a **user-chosen** password is not a default credential.

AL1 evidence: if any default accounts exist on public interfaces, confirm default credentials are not used. Velvet Elves has **no default accounts** on public interfaces.

Public interfaces in scope: `https://app.velvetelves.com/`, `https://app.stage.velvetelves.com/`, `https://api.prod.velvetelves.com/`, `https://api.stage.velvetelves.com/`. Vendor / client / FSBO surfaces use the same SPA auth. Help center and marketing site have no login form.

## How accounts are created

There is no bootstrap script, SQL seed, or documented demo login that inserts a known username/password pair.

- **Self-register:** `POST /api/v1/users/register` → `AuthService.register` → `supabase.auth.sign_up` with the password the user typed. Roles that can self-sign-up: Agent, TeamLead, TransactionCoordinator, Admin (`SELF_SIGNUP_ROLES_NOW`). `DEFAULT_ACCOUNT_ROLE` on the register form is **Agent** — that is a role picker default, not a password.
- **Invite:** branded invite creates an Auth user **without** a password. `POST /invitations/accept/{token}` sets the password the invitee typed (`auth.admin.update_user_by_id` or `sign_up`).
- **Password reset:** user chooses a new password from a one-time recovery link.
- SQL migrations seed templates/content only. They do not `INSERT` into `auth.users` or store a password on `public.users`.

`AuthService` docstring: Supabase Auth owns every secret/credential.

## Login UI

`LoginPage` uses `react-hook-form` with **no** `defaultValues` for email or password. Placeholders only (`you@example.com`, `Enter your password`). Google Sign-in is authorization-code OAuth for that Google user — it is not a shared Velvet Elves password.

## Live check

Classic pair `admin@velvetelves.com` / `Admin` on staging login is rejected (401 Invalid email or password). The form does not ship those values.

## Portal comment

```
Velvet Elves does not ship default accounts or predefined username/password pairs on public interfaces (no Admin/Admin). Accounts are created only by self-register or invite accept; the user always chooses the password. Login and register forms start empty. A classic default pair is rejected. Google Sign-in is the user's Google account via OAuth, not a shared Velvet Elves password. SQL seeds do not insert passwords.
```
