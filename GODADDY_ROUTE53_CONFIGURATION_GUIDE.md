# GoDaddy Route 53 Configuration Guide

Date: 2026-06-29

Purpose:

- Provide simple GoDaddy-only instructions for moving `velvetelves.com` DNS hosting to AWS Route 53.
- The GoDaddy operator should only perform the steps below.
- AWS setup, Route 53 record creation, DNS verification, and application checks are outside the GoDaddy account holder's scope.

Reference:

- `GODADDY_TO_ROUTE53_MIGRATION_GUIDE.md`

---

## 1. Scope

This guide covers only GoDaddy configuration.

The GoDaddy operator will:

1. Confirm access to `velvetelves.com`.
2. Capture the current GoDaddy nameservers.
3. Export or screenshot all current DNS records.
4. Check whether DNSSEC is enabled.
5. Lower TTLs only if this guide or the migration schedule says to do so.
6. Replace GoDaddy nameservers with AWS Route 53 nameservers only during the scheduled migration window.
7. Restore the previous GoDaddy nameservers only if rollback is requested by the project owner.

The GoDaddy operator should not perform AWS tasks.

---

## 2. Do Not Change These Items

Do not do any of the following as part of this DNS hosting migration:

- Do not transfer the domain away from GoDaddy.
- Do not unlock the domain.
- Do not request an authorization or EPP code.
- Do not delete DNS records.
- Do not edit email records.
- Do not change `dev.velvetelves.com`.
- Do not enable or disable DNSSEC.
- Do not change nameservers before the scheduled migration window.
- Do not share GoDaddy passwords, 2FA codes, or private account details.

If GoDaddy asks about domain transfer, domain unlock, or authorization code, stop. That is not part of this migration.

---

## 3. Confirm GoDaddy Access

1. Log in to GoDaddy.
2. Open **Domain Portfolio**.
3. Select `velvetelves.com`.
4. Confirm that DNS and nameserver settings are visible.

Send this confirmation:

```text
I can access the GoDaddy DNS/nameserver settings for velvetelves.com.
```

---

## 4. Record Current GoDaddy Nameservers

Before any change, record the current nameservers exactly.

1. In GoDaddy, open **Domain Portfolio**.
2. Select `velvetelves.com`.
3. Open **DNS** or **Nameservers**.
4. Copy the current nameservers exactly.
5. Take a screenshot of the nameserver page.

Send this information:

```text
Current nameserver 1:
Current nameserver 2:
Current nameserver 3:
Current nameserver 4:
Captured by:
Captured at:
```

These values are required for rollback.

---

## 5. Export Or Screenshot DNS Records

Before nameservers are changed, capture all DNS records currently in GoDaddy.

1. In GoDaddy, open `velvetelves.com`.
2. Open **DNS**.
3. Go to the **Records** section.
4. Export the records if GoDaddy offers an export option.
5. If export is not available, take screenshots.
6. Scroll through the full page and capture every record.

Capture all visible record types, including:

```text
A
AAAA
CNAME
MX
TXT
SRV
CAA
NS
SOA
```

Make sure email-related records are included:

```text
MX
TXT records that start with v=spf1
DKIM records
_dmarc.velvetelves.com
Microsoft or Google verification TXT records
autodiscover
autoconfig
mail
smtp
imap
pop
webmail
```

Send the export or screenshots through the agreed secure channel.

Do not paste private verification TXT values into public chat.

---

## 6. Check DNSSEC

1. In GoDaddy, open `velvetelves.com`.
2. Look for **DNSSEC** in the domain or DNS settings.
3. Check whether DNSSEC is enabled or disabled.

Send one of these:

```text
DNSSEC is disabled for velvetelves.com.
```

or:

```text
DNSSEC is enabled for velvetelves.com.
```

If DNSSEC is enabled, stop. Do not change nameservers until a separate DNSSEC plan is provided.

---

## 7. Lower TTLs Only If Scheduled

TTL lowering is optional and should be done only if the migration schedule includes it.

If TTL lowering is scheduled:

1. Open the DNS records for `velvetelves.com`.
2. Set the specified non-email records to TTL `300` seconds if GoDaddy allows it.
3. Do not change record values.
4. Do not change email records.

Send this confirmation:

```text
Requested TTL changes are complete.
No DNS record values were changed.
```

---

## 8. Change Nameservers To Route 53

Only perform this step during the scheduled migration window.

The project owner will provide four AWS Route 53 nameservers before the migration window. They will look similar to:

```text
ns-000.awsdns-00.com
ns-000.awsdns-00.net
ns-000.awsdns-00.org
ns-000.awsdns-00.co.uk
```

Use the exact four nameservers provided for `velvetelves.com`.

Steps:

1. In GoDaddy, open **Domain Portfolio**.
2. Select `velvetelves.com`.
3. Open **DNS** or **Nameservers**.
4. Choose the option for custom nameservers.
5. Replace the current nameservers with the four AWS Route 53 nameservers.
6. Save.
7. Complete any GoDaddy confirmation or 2FA prompt.
8. Take a screenshot of the saved nameserver page.

Important:

- Enter all four Route 53 nameservers.
- Do not enter only one or two.
- Do not add `https://`.
- Do not add a path.
- If GoDaddy rejects a trailing dot, remove the trailing dot.

Correct:

```text
ns-123.awsdns-45.com
```

Incorrect:

```text
https://ns-123.awsdns-45.com
ns-123.awsdns-45.com/
```

Send this confirmation:

```text
The GoDaddy nameservers for velvetelves.com have been changed to the four Route 53 nameservers.
Saved at:
```

Attach the screenshot if possible.

---

## 9. Rollback Nameservers

Only perform rollback if the project owner requests it.

Rollback means restoring the old GoDaddy nameservers recorded in Section 4.

Steps:

1. In GoDaddy, open **Domain Portfolio**.
2. Select `velvetelves.com`.
3. Open **DNS** or **Nameservers**.
4. Replace the Route 53 nameservers with the previous GoDaddy nameservers.
5. Save.
6. Complete any GoDaddy confirmation or 2FA prompt.
7. Take a screenshot of the restored nameserver page.

Send this confirmation:

```text
Rollback is complete. The previous GoDaddy nameservers have been restored.
Saved at:
```

Attach the screenshot if possible.

---

## 10. Stop Conditions

Stop and do not make changes if:

- DNS settings cannot be found.
- Current nameservers cannot be found.
- DNS records cannot be fully exported or screenshotted.
- DNSSEC is enabled.
- GoDaddy shows a warning about email.
- GoDaddy asks to unlock the domain.
- GoDaddy asks for an authorization or EPP code.
- GoDaddy asks to delete records.
- The nameserver fields do not match the instructions above.
- There is any uncertainty about the change.

When unsure, stop. Do not guess. Send a screenshot of the GoDaddy screen and wait for updated instructions from the project owner.
