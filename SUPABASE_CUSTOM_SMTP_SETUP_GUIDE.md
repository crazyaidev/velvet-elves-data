# Supabase Custom SMTP Setup Guide for Velvet Elves

This guide explains how to configure **SendGrid as the custom SMTP provider for Supabase Auth** in a way that is easy to follow, even if you are new to Supabase.

It is written specifically for your current setup:

- one Supabase project/account for **local testing**
- one Supabase project/account for **production**

Important: Supabase SMTP settings are configured **per project**, not globally. That means you must set up SMTP **twice**:

1. once in the local-testing Supabase project
2. once in the production Supabase project

If you literally use two different Supabase logins, sign in to each account separately and repeat the steps. If you use one login with two projects, the idea is the same: each project has its own Auth settings.

## What this solves

Without custom SMTP, Supabase Auth uses its built-in email sender. That default sender is only meant for testing, can refuse non-team email addresses, and has a very small sending limit. Custom SMTP moves email delivery to your own SendGrid account so registration emails, password resets, invites, and email confirmation messages are sent using your own sender reputation.

## Very important project-specific note

In this codebase, the backend already has a `SENDGRID_API_KEY` variable in its `.env`, but that **does not automatically configure Supabase Auth**. Supabase Auth sends its own emails from inside the Supabase project dashboard settings. In other words:

- backend `.env` settings do not replace Supabase SMTP settings
- you still must configure SMTP inside **each Supabase project**

## Velvet Elves URLs used by this guide

This project currently uses these frontend routes:

- local frontend base URL: `http://localhost:5173`
- email confirmation page: `/auth/confirm`
- reset password page: `/reset-password`

For production, this guide uses:

- production frontend base URL: `https://app.velvetelves.com`

If your real production frontend URL is different, replace `https://app.velvetelves.com` everywhere in this document with the correct live URL.

## Recommended environment split

Use separate SMTP credentials and separate Supabase configuration for local testing and production. Even if both environments use the same SendGrid account, do **not** share the same API key between them.

| Area | Local testing Supabase project | Production Supabase project |
| --- | --- | --- |
| Purpose | Developer testing and QA | Real users and live traffic |
| Supabase Site URL | `http://localhost:5173` | `https://app.velvetelves.com` |
| Redirect URLs | `http://localhost:5173/**` | exact production URLs, or `https://app.velvetelves.com/**` if needed |
| SendGrid API key | separate key named something like `supabase-auth-local` | separate key named something like `supabase-auth-prod` |
| Sender name | `Velvet Elves Local` or `Velvet Elves Dev` | `Velvet Elves` |
| From address | `no-reply-local@auth.velvetelves.com` | `no-reply@auth.velvetelves.com` |
| Email rate limit | keep low on purpose | raise based on expected real traffic |

## Before you begin

Make sure you have these things ready:

1. A working SendGrid account.
2. A domain you control, such as `velvetelves.com`.
3. DNS access for that domain.
4. Access to both Supabase environments.
5. The actual production frontend URL.

## Recommended SendGrid structure

The cleanest beginner-friendly setup is this:

- one SendGrid account
- one authenticated sending domain or subdomain for auth mail
- two separate API keys
- one key for local Supabase
- one key for production Supabase

### Good sender naming pattern

Use auth-only sender addresses so your authentication emails stay separate from marketing or regular business email.

Recommended example:

- local: `no-reply-local@auth.velvetelves.com`
- production: `no-reply@auth.velvetelves.com`

If you want even stricter separation, you can use two different authenticated subdomains:

- local: `auth-local.velvetelves.com`
- production: `auth.velvetelves.com`

That is optional, but it is a nice long-term setup.

## Part 1: Prepare SendGrid first

Do this one time before touching Supabase.

### Step 1: Authenticate your domain in SendGrid

In SendGrid, do **Domain Authentication**, not just basic sender verification, if you want a proper long-term setup.

Why this matters:

- it improves deliverability
- it lets you send from addresses on your own domain
- it avoids "unverified sender" errors later

If you only verify a single sender address, local tests may work, but production deliverability will usually be weaker.

### Step 2: Create two separate SendGrid API keys

In SendGrid:

1. Open **Settings -> API Keys**.
2. Create one key for local, for example `supabase-auth-local`.
3. Create one key for production, for example `supabase-auth-prod`.
4. Save both keys in a secure password manager or secret manager.

Do not reuse the same key in both environments.

If one environment is ever compromised or rotated, you do not want it to break the other environment.

### Step 3: Know the exact SendGrid SMTP values

These are the values Supabase needs for SendGrid SMTP:

| Supabase SMTP field | SendGrid value |
| --- | --- |
| SMTP host | `smtp.sendgrid.net` |
| SMTP port | `587` |
| SMTP user | `apikey` |
| SMTP password | your SendGrid API key |
| Sender name | your display name, for example `Velvet Elves` |
| Admin email / From email | a verified sender on your authenticated domain |

Important beginner clarification:

- `apikey` is literally the username value
- the actual SendGrid API key goes in the password field
- the From email must match a verified sender identity in SendGrid

## Part 2: Configure the local-testing Supabase project

This section is for your **local Supabase account/project**.

The goal here is:

- emails should send from your SendGrid local key
- links in emails should bring you back to `http://localhost:5173`
- testing traffic should stay separate from production traffic

### Step 1: Open the correct Supabase project

Sign in to the Supabase account that you use for local testing and open the local-testing project.

Pause here and double-check that you are not in production.

A very common mistake is changing SMTP settings in the wrong project.

### Step 2: Configure Auth URL settings for local

In the Supabase dashboard, go to the Auth URL configuration area.

Depending on Supabase UI changes, the exact label may be something like:

- **Authentication -> URL Configuration**
- or a similar Auth settings page that contains **Site URL** and **Redirect URLs**

Set these values:

| Setting | Local value |
| --- | --- |
| Site URL | `http://localhost:5173` |
| Redirect URL | `http://localhost:5173/**` |

Why this matters:

- the **Site URL** is the default destination if no redirect is explicitly provided
- the **Redirect URLs** list allows Supabase to redirect users back to your app after email confirmation, password reset, invite acceptance, or other auth flows

For this project, `http://localhost:5173/**` is the simplest and safest local setup because it covers:

- `http://localhost:5173/auth/confirm`
- `http://localhost:5173/reset-password`
- other local auth paths under the same frontend

If you also sometimes run the frontend on another port, add that port too.

### Step 3: Configure custom SMTP in local Supabase

Now go to the Supabase SMTP settings page.

Depending on the current dashboard layout, this is usually under Authentication in a section such as:

- **Authentication -> Emails -> SMTP Settings**
- or a general **Authentication settings** page with SMTP fields

Enable custom SMTP, then enter:

| Field | Local testing value |
| --- | --- |
| SMTP host | `smtp.sendgrid.net` |
| SMTP port | `587` |
| SMTP user | `apikey` |
| SMTP password | the value of your `supabase-auth-local` SendGrid API key |
| Sender name | `Velvet Elves Local` |
| Admin email / From email | `no-reply-local@auth.velvetelves.com` |

If your chosen local sender address is different, that is fine. Just make sure it is valid in SendGrid.

### Step 4: Save and send a test email

Save the SMTP settings in Supabase.

If Supabase offers a test-send or validation action in the UI, use it.

If there is no built-in test button, do a real app test:

1. register a new user in your local app
2. request a password reset
3. check that the email arrives
4. check that clicking the link returns to `http://localhost:5173`

### Step 5: Decide how strict local email confirmation should be

In Supabase Auth provider settings for email/password auth, you can control whether users must confirm email before logging in.

For local testing, you have two reasonable options:

1. **Recommended for realistic testing**: keep email confirmation enabled.
2. **Recommended only for faster dev loops**: temporarily disable email confirmation in the local project.

If your goal is to test the full real user flow, leave it enabled in local so local behavior stays close to production.

### Step 6: Set conservative local rate limits

After custom SMTP is enabled, Supabase starts with a low auth email rate limit by default. Go to:

- **Authentication -> Rate Limits**

For local testing, keeping the email-send limit low is a good idea. You are not serving real traffic there.

Suggested local approach:

- keep the project-wide auth email limit low
- do not use production-sized limits in local
- leave per-user cooldowns in place unless you are intentionally load testing

This prevents accidental email storms during development.

## Part 3: Configure the production Supabase project

This section is for your **production Supabase account/project**.

The goal here is:

- real users receive production emails
- links go to the real live app
- production sender identity stays clean and trustworthy

### Step 1: Open the correct production project

Sign in to your production Supabase account/project.

Again, pause and confirm you are truly in production before editing anything.

### Step 2: Configure Auth URL settings for production

Open the Auth URL configuration area in the production Supabase project.

Set:

| Setting | Production value |
| --- | --- |
| Site URL | `https://app.velvetelves.com` |

For Redirect URLs, the safest production approach is to add the exact paths you need whenever possible.

Recommended production redirect URLs:

- `https://app.velvetelves.com/auth/confirm`
- `https://app.velvetelves.com/reset-password`
- `https://app.velvetelves.com/**`

Notes:

- the wildcard entry is useful if invite flows or future auth pages use additional paths
- if you prefer a tighter production policy, keep exact paths only and add new ones deliberately as your auth flows grow

If your actual live domain is not `app.velvetelves.com`, replace it with the correct production URL.

### Step 3: Configure custom SMTP in production

In the production Supabase project, open the SMTP settings section and enable custom SMTP.

Enter:

| Field | Production value |
| --- | --- |
| SMTP host | `smtp.sendgrid.net` |
| SMTP port | `587` |
| SMTP user | `apikey` |
| SMTP password | the value of your `supabase-auth-prod` SendGrid API key |
| Sender name | `Velvet Elves` |
| Admin email / From email | `no-reply@auth.velvetelves.com` |

Do not copy the local API key into production.

### Step 4: Keep production email confirmation enabled

For production, the usual recommendation is:

- keep email confirmation enabled
- keep secure email change protections enabled

This is the safer default for real users.

### Step 5: Raise production auth email limits to a realistic number

After SMTP is working in production, go to:

- **Authentication -> Rate Limits**

Supabase's default custom-SMTP auth email limit starts low, so you may need to raise it for a real launch.

Think about:

- expected signups per hour
- password reset volume
- invite volume
- support/admin traffic

Do not leave production at a tiny limit if you expect real users to sign up.

At the same time, do not set it absurdly high without spam protection. Increase it to a number that matches expected traffic, then adjust as you learn from real usage.

## Part 4: Keep Supabase and app configuration aligned

Supabase SMTP is only one side of the setup. Your application environment values should still point to the correct frontend per environment.

### Local app alignment

For local development, your backend should continue to point to the local frontend:

```env
FRONTEND_URL=http://localhost:5173
```

### Production app alignment

For production, your backend should point to the real frontend URL:

```env
FRONTEND_URL=https://app.velvetelves.com
```

If production `FRONTEND_URL` points to localhost, password reset links and invite links may send users to the wrong place.

## Part 5: The easiest safe setup for a beginner

If you want the simplest reliable setup, do exactly this:

1. Authenticate `auth.velvetelves.com` in SendGrid.
2. Create two SendGrid API keys:
   - `supabase-auth-local`
   - `supabase-auth-prod`
3. In local Supabase:
   - Site URL: `http://localhost:5173`
   - Redirect URL: `http://localhost:5173/**`
   - SMTP host: `smtp.sendgrid.net`
   - SMTP port: `587`
   - SMTP user: `apikey`
   - SMTP password: local SendGrid key
   - Sender name: `Velvet Elves Local`
   - Admin email: `no-reply-local@auth.velvetelves.com`
4. In production Supabase:
   - Site URL: `https://app.velvetelves.com`
   - Redirect URLs:
     - `https://app.velvetelves.com/auth/confirm`
     - `https://app.velvetelves.com/reset-password`
     - `https://app.velvetelves.com/**`
   - SMTP host: `smtp.sendgrid.net`
   - SMTP port: `587`
   - SMTP user: `apikey`
   - SMTP password: production SendGrid key
   - Sender name: `Velvet Elves`
   - Admin email: `no-reply@auth.velvetelves.com`

If you follow only those steps, you will already be in good shape.

## Part 6: Testing checklist for local

After local SMTP is configured, test these one by one:

1. Register a brand-new test account.
2. Confirm that the email arrives in the mailbox.
3. Open the link and confirm it returns to `http://localhost:5173`.
4. Request a password reset.
5. Confirm that the reset email arrives.
6. Open the reset link and confirm it returns to the local app.
7. If your app uses invites, test an invite flow too.

If any email opens the production site instead of localhost, the local Supabase project still has the wrong Site URL or Redirect URLs configured.

## Part 7: Testing checklist for production

Do not test production with a real customer first.

Instead:

1. create a dedicated internal test mailbox
2. register a fresh test user in production
3. confirm the production email arrives
4. click the confirmation link
5. verify it lands on the live production app
6. request a password reset
7. verify the reset link also lands on the live production app

If any production email opens localhost, production URL configuration is wrong.

## Part 8: Troubleshooting guide

### Problem: `email rate limit exceeded`

Possible causes:

- custom SMTP was not actually enabled in that Supabase project
- custom SMTP was enabled, but the rate limit is still too low
- you changed one project but are testing against the other one

What to do:

1. confirm you are in the correct Supabase project
2. confirm custom SMTP is enabled there
3. confirm the SMTP settings are saved
4. review **Authentication -> Rate Limits**

### Problem: `Email address not authorized`

This usually means the project is still using Supabase's default email sender instead of your own custom SMTP setup.

What to do:

1. open SMTP settings in that exact project
2. confirm custom SMTP is enabled
3. confirm the host is `smtp.sendgrid.net`
4. save again and retest

### Problem: `535 Authentication failed`

This usually means the SendGrid SMTP credentials are wrong.

Check all of these:

- host is `smtp.sendgrid.net`
- port is `587`
- username is literally `apikey`
- password is the full SendGrid API key
- the API key has not been revoked or rotated

### Problem: sender identity / from-address errors

This usually means the From email in Supabase does not match a verified sender in SendGrid.

What to do:

1. verify the domain or sender in SendGrid
2. confirm the exact From address in Supabase
3. avoid random Gmail or unverified addresses

### Problem: email arrives, but clicking it opens the wrong environment

Examples:

- local emails open production
- production emails open localhost

This is almost always a **Site URL or Redirect URL** problem in the Supabase project you are testing.

Fix:

1. open the matching Supabase project
2. correct the Site URL
3. correct the Redirect URLs
4. send a fresh email and test again

### Problem: no email arrives at all

Check both places:

1. Supabase Auth logs
2. SendGrid activity / message logs

A good rule:

- if Supabase accepted the auth action but SendGrid rejected delivery, the issue is usually sender identity, credentials, or SendGrid account policy
- if Supabase itself throws an auth error before sending, the issue is usually project configuration inside Supabase

## Part 9: Best practices you should keep

### 1. Never share SMTP keys between local and production

Always keep:

- one key for local
- one key for production

### 2. Keep auth email separate from marketing email

Use an auth-focused sender such as:

- `no-reply@auth.velvetelves.com`

Do not mix signup/reset emails with newsletters or promotions.

### 3. Keep local rate limits low

Local environments are easier to abuse accidentally. A bug or test loop can send many emails quickly.

### 4. Keep production confirmation enabled

It is safer for real users.

### 5. Rotate keys carefully

If you ever rotate SendGrid credentials:

1. create the new key in SendGrid
2. update local Supabase if needed
3. test local
4. update production Supabase
5. test production
6. revoke the old key only after both environments work

## Part 10: Optional advanced note about local Supabase CLI

This guide assumes your "local environment" means a separate Supabase cloud project used for testing.

If you later switch to truly local Supabase development using the Supabase CLI, email behavior is different because local Auth email testing can be captured by Mailpit instead of SendGrid. In that case, you may not need custom SMTP for the CLI-only workflow. For your current two-account setup, though, this guide is the correct approach.

## Quick copy-paste summary

### Local testing Supabase project

| Setting | Value |
| --- | --- |
| Site URL | `http://localhost:5173` |
| Redirect URL | `http://localhost:5173/**` |
| SMTP host | `smtp.sendgrid.net` |
| SMTP port | `587` |
| SMTP user | `apikey` |
| SMTP password | local SendGrid API key |
| Sender name | `Velvet Elves Local` |
| Admin email | `no-reply-local@auth.velvetelves.com` |

### Production Supabase project

| Setting | Value |
| --- | --- |
| Site URL | `https://app.velvetelves.com` |
| Redirect URLs | `https://app.velvetelves.com/auth/confirm`, `https://app.velvetelves.com/reset-password`, `https://app.velvetelves.com/**` |
| SMTP host | `smtp.sendgrid.net` |
| SMTP port | `587` |
| SMTP user | `apikey` |
| SMTP password | production SendGrid API key |
| Sender name | `Velvet Elves` |
| Admin email | `no-reply@auth.velvetelves.com` |

## Final reminder

Think of this as two separate email systems:

- local Supabase sends local/test auth email
- production Supabase sends real/live auth email

Even if both systems use SendGrid, they should not share the same API key, and they should not point to the wrong frontend URL.
