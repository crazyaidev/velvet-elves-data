# SendGrid Settings Guide for Velvet Elves

Last reviewed: 2026-04-24

This guide explains the **SendGrid side** of the setup in a simple step-by-step format.

This guide is for these two environments only:

- **Local development**: `http://localhost:5173`
- **Shared development server**: `http://dev.velvetelves.com`

This guide does **not** cover a live production environment yet.

If you also need the Supabase setup, see:

- `SUPABASE_CUSTOM_SMTP_SETUP_GUIDE.md`

## The final setup we want

Use these exact values:

| Item | Local development | Shared development server |
| --- | --- | --- |
| Authenticated sending subdomain | `auth.velvetelves.com` | `auth.velvetelves.com` |
| API key name | `supabase-auth-local` | `supabase-auth-dev` |
| Sender name | `Velvet Elves Local` | `Velvet Elves Development` |
| Sender email | `no-reply-local@auth.velvetelves.com` | `no-reply-dev@auth.velvetelves.com` |
| SMTP host | `smtp.sendgrid.net` | `smtp.sendgrid.net` |
| SMTP port | `587` | `587` |
| SMTP username | `apikey` | `apikey` |

## What is already completed

You already have an **existing verified SendGrid domain setup** for `velvetelves.com`.

Based on the current SendGrid screen, that older verified setup appears as:

- `em9714.velvetelves.com`

That existing verified setup should **stay in place**.

For the current work, you are adding a **second SendGrid authentication setup** for:

- `auth.velvetelves.com`

So after this work is finished, it is normal to have:

- the older verified setup for `velvetelves.com`
- the new verified setup for `auth.velvetelves.com`

This means you are **adding**, not replacing.

## Part 1: One-time SendGrid setup

Do this part **once** in SendGrid before setting up either environment.

### Step 1: Sign in to SendGrid

1. Open SendGrid.
2. Sign in to the correct account.

### Step 2: Start domain authentication

1. In the left menu, open `Settings`.
2. Click `Sender Authentication`.
3. In the `Domain Authentication` section, click `Get Started`.

### Step 3: Choose the exact values for domain authentication

On the SendGrid setup screens, choose these values:

- DNS host:
  - choose `GoDaddy` **if GoDaddy is hosting the DNS for `velvetelves.com`**
  - if DNS is hosted somewhere else, choose the real DNS host instead
- Link Branding: `No`
- Domain you send from: `auth.velvetelves.com`
- Use automated security: `On`
- Use custom return path: `Off`
- Use custom DKIM selector: `Off`
- Make domain EU-pinned: `Off`

Important:

- `Link Branding` is **not required** for this setup
- for the current project, the recommended sending subdomain is `auth.velvetelves.com`
- even though `velvetelves.com` is already verified, still choose `auth.velvetelves.com` here because the new sender emails will use `@auth.velvetelves.com`

### Step 4: Add the DNS records

After the previous step, SendGrid will show DNS records that must be added.

### Step 4A: Very important safety rule before changing GoDaddy

Based on the current GoDaddy DNS list for `velvetelves.com`, you already have many records in place.

You also already have an older verified SendGrid setup for the root domain.

That means the goal is **not** to replace the old records.

The goal is to **add new records for the `auth` subdomain only**.

Do **not** delete or edit these existing records unless you are intentionally replacing them for a separate reason:

- `A` record: `@`
- `A` record: `api`
- `A` record: `dev`
- `A` record: `login`
- `NS` records
- `SOA` record
- `MX` records
- `TXT` record: `@`
- `TXT` record: `_dmarc`
- `SRV` record: `_autodiscover._tcp`
- `CNAME` record: `61966822`
- `CNAME` record: `em9714`
- `CNAME` record: `email`
- `CNAME` record: `pay`
- `CNAME` record: `s1._domainkey`
- `CNAME` record: `s2._domainkey`
- `CNAME` record: `url647`

Why this matters:

- the existing records above are for the root domain or other services
- the older verified SendGrid setup for `velvetelves.com` should stay active
- the new SendGrid records we are adding are for the `auth` subdomain
- `s1._domainkey` and `s1._domainkey.auth` are **different**
- `_dmarc` and `_dmarc.auth` are **different**
- `em9714` and `em548.auth` are **different**

So the new records should live **alongside** the existing ones, not replace them.

### Step 4B: Add these new `auth` records only

Based on the current SendGrid screen for `auth.velvetelves.com`, these are the exact new records being shown right now:

| Record type | SendGrid shows this host | Enter this in GoDaddy `Name` / `Host` | Enter this in GoDaddy `Value` / `Points to` |
| --- | --- | --- | --- |
| `CNAME` | `em548.auth.velvetelves.com` | `em548.auth` | `u61966822.wl073.sendgrid.net` |
| `CNAME` | `s1._domainkey.auth.velvetelves.com` | `s1._domainkey.auth` | `s1.domainkey.u61966822.wl073.sendgrid.net` |
| `CNAME` | `s2._domainkey.auth.velvetelves.com` | `s2._domainkey.auth` | `s2.domainkey.u61966822.wl073.sendgrid.net` |
| `TXT` | `_dmarc.auth.velvetelves.com` | `_dmarc.auth` | `v=DMARC1; p=none;` |

Important:

- these are the values shown in the current screenshot
- if SendGrid later shows different values, follow the newest SendGrid screen
- these records should be **added as new entries**
- they should **not** replace your existing root-domain SendGrid records

#### If SendGrid offers automatic GoDaddy setup

Use it if:

- GoDaddy is the DNS host
- the automatic setup option appears
- it completes successfully

#### If you need to add the records manually in GoDaddy

1. Sign in to GoDaddy.
2. Open `Domain Portfolio`.
3. Select the domain `velvetelves.com`.
4. Click `DNS`.
5. Before changing anything, check whether these exact `Name / Host` values already exist:
   - `em548.auth`
   - `s1._domainkey.auth`
   - `s2._domainkey.auth`
   - `_dmarc.auth`
6. If those exact names do **not** exist yet, click `Add New Record`.
7. Add these 4 records one by one.

Important:

- if GoDaddy already has a record with the exact same `Type` and `Name`, do **not** blindly create another one
- first compare the existing value with the value shown in SendGrid
- if the value already matches SendGrid, leave that record as it is
- if the value is different, stop and verify which value is correct before changing anything
- do **not** edit records like `s1._domainkey`, `s2._domainkey`, `_dmarc`, or `em9714` when the new record should be `s1._domainkey.auth`, `s2._domainkey.auth`, `_dmarc.auth`, or `em548.auth`

Use these rules when entering the values:

- **Type**:
  - use the exact record type shown by SendGrid
  - for the current setup, add:
    - `CNAME`
    - `CNAME`
    - `CNAME`
    - `TXT`
- **Name / Host**:
  - enter only the host part, not the full domain
  - for the current setup, enter:
    - `em548.auth`
    - `s1._domainkey.auth`
    - `s2._domainkey.auth`
    - `_dmarc.auth`
- **Value / Points to**:
  - for the current setup, enter:
    - `u61966822.wl073.sendgrid.net`
    - `s1.domainkey.u61966822.wl073.sendgrid.net`
    - `s2.domainkey.u61966822.wl073.sendgrid.net`
    - `v=DMARC1; p=none;`
- **TTL**:
  - leave the default value
  - or use `1 hour` if GoDaddy asks you to choose one

### Step 4C: What to enter in GoDaddy for each new record

Create these records exactly like this:

1. First record
   - Type: `CNAME`
   - Name / Host: `em548.auth`
   - Value / Points to: `u61966822.wl073.sendgrid.net`
   - TTL: default or `1 hour`

2. Second record
   - Type: `CNAME`
   - Name / Host: `s1._domainkey.auth`
   - Value / Points to: `s1.domainkey.u61966822.wl073.sendgrid.net`
   - TTL: default or `1 hour`

3. Third record
   - Type: `CNAME`
   - Name / Host: `s2._domainkey.auth`
   - Value / Points to: `s2.domainkey.u61966822.wl073.sendgrid.net`
   - TTL: default or `1 hour`

4. Fourth record
   - Type: `TXT`
   - Name / Host: `_dmarc.auth`
   - Value / Points to: `v=DMARC1; p=none;`
   - TTL: default or `1 hour`

### Step 5: Verify the domain

1. Return to SendGrid.
2. Click `Verify`.
3. Wait for verification to finish.

Notes:

- some DNS changes work quickly
- full DNS propagation can take up to 48 hours
- during verification, keep all of the older DNS records in place
- do not remove any root-domain SendGrid records just because you added `auth` subdomain records
- it is okay if SendGrid ends up showing both the older verified root-domain setup and the new verified `auth` subdomain setup

### Step 6: Create the API key for local development

1. In SendGrid, open `Settings -> API Keys`.
2. Click `Create API Key`.
3. Enter this name:
   - `supabase-auth-local`
4. Choose this permission type:
   - `Custom Access`
5. In the permissions list, turn on:
   - `Mail Send`
6. Click `Create & View`.
7. Copy the API key and save it somewhere safe.

Important:

- SendGrid only shows the full API key value one time
- if you lose it, create a new one

### Step 7: Create the API key for the shared development server

1. In SendGrid, open `Settings -> API Keys`.
2. Click `Create API Key`.
3. Enter this name:
   - `supabase-auth-dev`
4. Choose this permission type:
   - `Custom Access`
5. In the permissions list, turn on:
   - `Mail Send`
6. Click `Create & View`.
7. Copy the API key and save it somewhere safe.

## Part 2: Exact values for local development

Use this section when you configure the **local** environment.

### Step 1: Use the correct sender identity

Set these exact values:

- Sender name: `Velvet Elves Local`
- Sender email: `no-reply-local@auth.velvetelves.com`

### Step 2: Use the correct API key

Use this exact API key:

- API key name: `supabase-auth-local`

### Step 3: Use the correct SMTP values

Set these exact values:

- SMTP host: `smtp.sendgrid.net`
- SMTP port: `587`
- SMTP username: `apikey`
- SMTP password: the value of the `supabase-auth-local` API key

Important:

- the username is literally `apikey`
- the API key itself goes into the password field

### Step 4: Optional reply-to address

If you want replies to go to a monitored inbox, use:

- Reply-To: `support@velvetelves.com`

This is optional.

### Step 5: Local checklist

Before moving on, confirm all of these:

- domain authentication is verified in SendGrid
- sender name is `Velvet Elves Local`
- sender email is `no-reply-local@auth.velvetelves.com`
- API key name is `supabase-auth-local`
- SMTP host is `smtp.sendgrid.net`
- SMTP port is `587`
- SMTP username is `apikey`

## Part 3: Exact values for the shared development server

Use this section when you configure the **shared development server** at `http://dev.velvetelves.com`.

### Step 1: Use the correct sender identity

Set these exact values:

- Sender name: `Velvet Elves Development`
- Sender email: `no-reply-dev@auth.velvetelves.com`

### Step 2: Use the correct API key

Use this exact API key:

- API key name: `supabase-auth-dev`

### Step 3: Use the correct SMTP values

Set these exact values:

- SMTP host: `smtp.sendgrid.net`
- SMTP port: `587`
- SMTP username: `apikey`
- SMTP password: the value of the `supabase-auth-dev` API key

Important:

- the username is literally `apikey`
- the API key itself goes into the password field

### Step 4: Optional reply-to address

If you want replies to go to a monitored inbox, use:

- Reply-To: `support@velvetelves.com`

This is optional.

### Step 5: Shared development server checklist

Before moving on, confirm all of these:

- domain authentication is verified in SendGrid
- sender name is `Velvet Elves Development`
- sender email is `no-reply-dev@auth.velvetelves.com`
- API key name is `supabase-auth-dev`
- SMTP host is `smtp.sendgrid.net`
- SMTP port is `587`
- SMTP username is `apikey`

## Part 4: Most common mistakes

### Mistake 1: Using the same API key for both environments

Do **not** do this.

Use:

- `supabase-auth-local` for local development
- `supabase-auth-dev` for the shared development server

### Mistake 2: Using the wrong sender email

If you authenticate `auth.velvetelves.com`, the sender email should match it.

Use:

- `no-reply-local@auth.velvetelves.com`
- `no-reply-dev@auth.velvetelves.com`

### Mistake 3: Entering the full hostname in GoDaddy's Name field

Wrong example:

- `em548.auth.velvetelves.com`

Correct example:

- `em548.auth`

### Mistake 3A: Editing an old root-domain record instead of adding a new `auth` record

Do **not** replace:

- `s1._domainkey`
- `s2._domainkey`
- `_dmarc`
- `em9714`

with:

- `s1._domainkey.auth`
- `s2._domainkey.auth`
- `_dmarc.auth`
- `em548.auth`

Those are different records.

The new `auth` records should be added in addition to the old ones.

### Mistake 4: Putting the API key in the SMTP username field

Do **not** do this.

Use:

- SMTP username: `apikey`
- SMTP password: your real SendGrid API key

### Mistake 5: Thinking Link Branding is required

It is **not** required for this setup.

For now, choose:

- Link Branding: `No`

## Official references

- Twilio SendGrid domain authentication:
  - `https://www.twilio.com/docs/sendgrid/ui/account-and-settings/how-to-set-up-domain-authentication/`
- Twilio SendGrid API keys:
  - `https://www.twilio.com/docs/sendgrid/ui/account-and-settings/api-keys/`
- Twilio SendGrid SMTP integration:
  - `https://www.twilio.com/docs/sendgrid/for-developers/sending-email/integrating-with-the-smtp-api`
- Twilio SendGrid subdomain authentication guidance:
  - `https://support.sendgrid.com/hc/en-us/articles/19130282201883-How-to-authenticate-and-send-from-a-Subdomain`
- GoDaddy DNS record management:
  - `https://www.godaddy.com/help/manage-dns-records-680`
- GoDaddy CNAME record setup:
  - `https://help-center.dc-aws.godaddy.com/help/add-a-cname-record-19236`
