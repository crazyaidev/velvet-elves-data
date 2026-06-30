# Velvet Elves - GoDaddy to AWS Route 53 Migration Guide

Date: 2026-06-26

Status: Operational runbook. Do not execute during an app/API cutover unless explicitly scheduled.

Goal:

- Move authoritative DNS hosting for `velvetelves.com` from GoDaddy to AWS Route 53.
- Preserve company email, existing dev server behavior, and production availability.
- Optionally transfer domain registration from GoDaddy to Route 53 only after Route 53 DNS hosting is stable.

Important rule:

- Treat DNS hosting migration and domain registrar transfer as two separate projects.
- First migrate DNS hosting to Route 53.
- Verify marketing, app, API, help center, company email, and provider callbacks.
- Only then consider transferring the domain registrar from GoDaddy to Route 53.

---

## 1. Domain Model To Preserve

Keep this public domain model intact:

```text
dev.velvetelves.com              Existing dev server, unchanged

stage.velvetelves.com            Staging marketing site
app.stage.velvetelves.com        Staging product frontend
api.stage.velvetelves.com        Staging backend API
help.stage.velvetelves.com       Staging help center

velvetelves.com                  Production marketing site
app.velvetelves.com              Production product frontend
api.velvetelves.com              Production backend API
help.velvetelves.com             Production help center
```

Known Stage 0 DNS snapshot:

```text
velvetelves.com                  A      3.140.33.46       TTL 600
api.velvetelves.com              A      3.140.33.46       TTL 600
dev.velvetelves.com              A      18.188.144.155    TTL 600
```

Before migration, re-check this snapshot because DNS may have changed.

---

## 2. Migration Phases

| Phase | Purpose | Changes public DNS? | Changes registrar? |
| --- | --- | --- | --- |
| Phase A | Preparation and inventory | No | No |
| Phase B | Create Route 53 hosted zone | No | No |
| Phase C | Recreate and verify records in Route 53 | No | No |
| Phase D | Change GoDaddy nameservers to Route 53 | Yes | No |
| Phase E | Monitor and stabilize | No | No |
| Phase F | Optional registrar transfer to Route 53 | No, if DNS already migrated | Yes |

Do not start Phase F until Phase E has been stable for the agreed confidence window.

Recommended confidence window before registrar transfer:

```text
Minimum: 7 days
Preferred: 14 days
```

---

## 3. Required Access

Confirm access before making changes.

| Access | Required for | Verification |
| --- | --- | --- |
| GoDaddy admin | Export records, lower TTLs, change nameservers, rollback | Can access Domain Portfolio and DNS settings |
| AWS account `388482955098` | Create Route 53 hosted zone and records | `aws sts get-caller-identity` works |
| Email admin | Verify MX/SPF/DKIM/DMARC and test mail flow | Can inspect email provider DNS requirements |
| Provider dashboards | OAuth/webhook verification | Supabase, Google, Microsoft, Stripe, DocuSign |
| Internal approver | Production DNS change authorization | Written approval in chat/ticket |

Stop if any required access is missing.

---

## 4. Phase A - Pre-Migration Inventory

Goal: capture the current GoDaddy DNS state and define rollback.

### 4.1 Record Current Nameservers

In GoDaddy:

1. Open Domain Portfolio.
2. Select `velvetelves.com`.
3. Open DNS / Nameservers.
4. Record the current GoDaddy nameservers exactly.

Save them here before migration:

```text
Current nameserver 1: <fill-in>
Current nameserver 2: <fill-in>
Current nameserver 3: <fill-in-if-any>
Current nameserver 4: <fill-in-if-any>
Captured by: <name>
Captured at UTC: <timestamp>
```

Rollback depends on these values.

### 4.2 Export Or Screenshot All GoDaddy DNS Records

Capture every record from GoDaddy.

Required record types to inventory:

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

Email-sensitive records must be highlighted:

```text
MX
SPF TXT, usually v=spf1 ...
DKIM TXT or CNAME records
DMARC TXT at _dmarc.velvetelves.com
Microsoft or Google verification TXT records
autodiscover CNAME
autoconfig CNAME
Any mail, smtp, imap, pop, webmail, or provider-specific records
```

Do not proceed until the full GoDaddy zone is exported or screenshotted.

### 4.3 Verify Current Public DNS

Run from PowerShell:

```powershell
$Domain = "velvetelves.com"

Resolve-DnsName $Domain -Type NS
Resolve-DnsName $Domain -Type A
Resolve-DnsName "www.$Domain" -ErrorAction SilentlyContinue
Resolve-DnsName "app.$Domain" -ErrorAction SilentlyContinue
Resolve-DnsName "api.$Domain" -ErrorAction SilentlyContinue
Resolve-DnsName "dev.$Domain" -ErrorAction SilentlyContinue
Resolve-DnsName "help.$Domain" -ErrorAction SilentlyContinue
Resolve-DnsName $Domain -Type MX
Resolve-DnsName $Domain -Type TXT
Resolve-DnsName "_dmarc.$Domain" -Type TXT -ErrorAction SilentlyContinue
```

Save the command output outside the repo if it contains sensitive provider verification values.

### 4.4 Confirm DNSSEC State

In GoDaddy:

1. Check whether DNSSEC is enabled for `velvetelves.com`.
2. If DNSSEC is enabled, plan a separate DNSSEC step before nameserver migration.

Do not migrate nameservers while DS/DNSKEY records still point to the old DNS provider.

### 4.5 Lower GoDaddy TTLs

At least 24 hours before nameserver migration:

1. Lower app/API/marketing/help records that may change to `300` seconds.
2. Lower email records only if the email provider confirms this is safe.
3. If GoDaddy exposes nameserver TTL controls, lower NS TTL to a value between `60` and `900` seconds.

If NS TTL cannot be lowered in GoDaddy, assume some resolvers may keep old nameserver data for up to 48 hours.

Verification gate:

- Current nameservers are recorded.
- Full DNS record inventory exists.
- Email records are identified.
- DNSSEC state is known.
- TTL plan is complete.

Stop rule:

- Stop if email records are unclear.
- Stop if no one can restore GoDaddy nameservers during rollback.

---

## 5. Phase B - Create Route 53 Hosted Zone

Goal: create a public Route 53 hosted zone without changing live DNS.

### 5.1 Confirm AWS Identity

```powershell
aws sts get-caller-identity
aws configure get region
```

Expected account:

```text
388482955098
```

Route 53 hosted zones are global, but keep AWS CLI region set to the account standard, currently:

```text
us-east-2
```

### 5.2 Create Public Hosted Zone

```powershell
$Domain = "velvetelves.com"
$CallerReference = "velvet-elves-route53-$((Get-Date).ToUniversalTime().ToString('yyyyMMddHHmmss'))"

aws route53 create-hosted-zone `
  --name $Domain `
  --caller-reference $CallerReference `
  --hosted-zone-config Comment="Velvet Elves public DNS hosted zone",PrivateZone=false
```

Capture:

```text
Hosted zone ID: <fill-in>
Route 53 nameserver 1: <fill-in>
Route 53 nameserver 2: <fill-in>
Route 53 nameserver 3: <fill-in>
Route 53 nameserver 4: <fill-in>
```

### 5.3 Confirm Hosted Zone Exists

```powershell
aws route53 list-hosted-zones-by-name `
  --dns-name velvetelves.com `
  --output table
```

Verification gate:

- Hosted zone exists.
- Four Route 53 nameservers are recorded.
- GoDaddy nameservers have not been changed yet.

Stop rule:

- Stop if more than one active Route 53 hosted zone for `velvetelves.com` exists and ownership is unclear.

---

## 6. Phase C - Recreate Records In Route 53

Goal: reproduce the GoDaddy zone in Route 53 before changing nameservers.

### 6.1 Record Creation Rules

Use these rules:

- Copy all existing records unless there is a deliberate replacement.
- Preserve all email records exactly.
- Preserve `dev.velvetelves.com`.
- Do not create extra NS or SOA records beyond the defaults Route 53 created for the hosted zone.
- Use Route 53 alias records for AWS resources where appropriate.
- Use simple records first; add weighted/failover/latency routing later only if needed.

### 6.2 Recommended Route 53 Record Mapping

| Name | Type | Value | Notes |
| --- | --- | --- | --- |
| `velvetelves.com` | A or Alias | Current target or future marketing target | Use Route 53 Alias for CloudFront if marketing is on CloudFront |
| `app.velvetelves.com` | A Alias or CNAME | Production CloudFront target | Alias preferred in Route 53 |
| `api.velvetelves.com` | A Alias or CNAME | Production ALB target | Alias preferred in Route 53 |
| `dev.velvetelves.com` | A | `18.188.144.155` unless changed | Preserve existing dev server |
| `stage.velvetelves.com` | A Alias or CNAME | Staging marketing target | Only if staging marketing exists |
| `app.stage.velvetelves.com` | A Alias or CNAME | Staging CloudFront target | Product frontend staging |
| `api.stage.velvetelves.com` | A Alias or CNAME | Staging ALB target | Backend API staging |
| `help.velvetelves.com` | CNAME or Alias | Help center provider/CloudFront | Depends on help center hosting |
| `help.stage.velvetelves.com` | CNAME or Alias | Staging help center target | Depends on help center hosting |
| `velvetelves.com` | MX | Exact GoDaddy/email-provider values | Must preserve |
| `velvetelves.com` | TXT | SPF and provider verification | Must preserve |
| `_dmarc.velvetelves.com` | TXT | DMARC policy | Must preserve |
| DKIM names | TXT/CNAME | Exact provider values | Must preserve |

### 6.3 Example Route 53 Change Batch

Do not use this as-is. Replace values with the real GoDaddy inventory.

Create `aws-deploy-work\route53-initial-records.json`:

```json
{
  "Comment": "Initial Velvet Elves DNS records migrated from GoDaddy",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "dev.velvetelves.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "18.188.144.155"
          }
        ]
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "velvetelves.com",
        "Type": "MX",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "<priority> <mail-server-hostname>"
          }
        ]
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "velvetelves.com",
        "Type": "TXT",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "\"v=spf1 <provider-values>\""
          }
        ]
      }
    }
  ]
}
```

Apply:

```powershell
$HostedZoneId = "<route53-hosted-zone-id>"

aws route53 change-resource-record-sets `
  --hosted-zone-id $HostedZoneId `
  --change-batch file://aws-deploy-work/route53-initial-records.json
```

### 6.4 Verify Route 53 Records Before Nameserver Switch

Pick one Route 53 nameserver from the hosted zone and query it directly:

```powershell
$Route53NameServer = "<one-route53-name-server>"

Resolve-DnsName velvetelves.com -Type A -Server $Route53NameServer
Resolve-DnsName api.velvetelves.com -Type A -Server $Route53NameServer
Resolve-DnsName dev.velvetelves.com -Type A -Server $Route53NameServer
Resolve-DnsName velvetelves.com -Type MX -Server $Route53NameServer
Resolve-DnsName velvetelves.com -Type TXT -Server $Route53NameServer
Resolve-DnsName _dmarc.velvetelves.com -Type TXT -Server $Route53NameServer
```

Also verify every provider-specific DNS record listed in the GoDaddy inventory.

Verification gate:

- Route 53 direct queries match the intended GoDaddy records.
- Email records match exactly.
- `dev.velvetelves.com` resolves correctly from Route 53 direct queries.
- App/API/stage/help records are present only if intentionally configured.

Stop rule:

- Stop if any MX, SPF, DKIM, DMARC, or verification record differs unexpectedly.

---

## 7. Phase D - Switch GoDaddy Nameservers To Route 53

Goal: make Route 53 authoritative for `velvetelves.com`.

### 7.1 Final Pre-Switch Checklist

Confirm:

- Route 53 hosted zone is complete.
- Route 53 direct queries are correct.
- Current GoDaddy nameservers are recorded for rollback.
- Route 53 nameservers are recorded.
- Company email owner is available for testing.
- AWS operator and GoDaddy operator are both available.
- No app/API production cutover is happening at the same time.

### 7.2 Change Nameservers In GoDaddy

In GoDaddy:

1. Open Domain Portfolio.
2. Select `velvetelves.com`.
3. Open DNS / Nameservers.
4. Choose the option to use custom nameservers.
5. Enter all four Route 53 nameservers from the hosted zone.
6. Save.
7. Complete any 2FA or identity verification prompts.

Do not delete the Route 53 hosted zone.

### 7.3 Verify Public Nameserver Change

Run periodically:

```powershell
Resolve-DnsName velvetelves.com -Type NS
```

Expected:

```text
The authoritative nameservers eventually become the four Route 53 nameservers.
```

Propagation may not be instant. Keep both GoDaddy and AWS operators available during the monitoring window.

Verification gate:

- Public NS lookup returns Route 53 nameservers from multiple networks/resolvers.
- Website/app/API/help/email smoke tests pass.

Stop rule:

- Roll back nameservers in GoDaddy if email or critical app traffic fails and cannot be fixed immediately in Route 53.

---

## 8. Phase E - Post-Switch Monitoring

Goal: prove Route 53 is serving production DNS safely.

### 8.1 Immediate Checks

Run:

```powershell
Resolve-DnsName velvetelves.com -Type NS
Resolve-DnsName velvetelves.com -Type A
Resolve-DnsName app.velvetelves.com -ErrorAction SilentlyContinue
Resolve-DnsName api.velvetelves.com -ErrorAction SilentlyContinue
Resolve-DnsName dev.velvetelves.com
Resolve-DnsName velvetelves.com -Type MX
Resolve-DnsName velvetelves.com -Type TXT
Resolve-DnsName _dmarc.velvetelves.com -Type TXT -ErrorAction SilentlyContinue
```

### 8.2 User-Facing Checks

Check:

- `https://velvetelves.com`
- `https://app.velvetelves.com`, if active
- `https://api.velvetelves.com/api/health`, if active
- `https://help.velvetelves.com`, if active
- `https://dev.velvetelves.com`

### 8.3 Email Checks

Perform all:

1. Send email from a company mailbox to an external address.
2. Reply from the external address to the company mailbox.
3. Send from another external address to the company mailbox.
4. Confirm SPF pass.
5. Confirm DKIM pass.
6. Confirm DMARC alignment/pass.
7. Confirm no bounce messages.
8. Confirm no Microsoft/Google admin warning if that provider is used.

### 8.4 Provider Checks

Confirm:

- Supabase Auth links still use expected URLs.
- Google OAuth redirect validation still passes.
- Microsoft OAuth redirect validation still passes.
- Stripe webhook endpoint still receives events.
- DocuSign Connect webhook still receives events.
- Gmail Pub/Sub endpoint remains valid.
- Microsoft Graph webhook endpoint remains valid.

### 8.5 Monitoring Timeline

```text
T+0 minutes: DNS and website smoke tests
T+15 minutes: Email send/receive tests
T+30 minutes: Provider callback spot checks
T+2 hours: Repeat DNS/email/app checks
T+24 hours: Repeat all critical checks
T+48 hours: Confirm no delayed resolver or email issues
T+7 days: Eligible to plan registrar transfer
```

### 8.6 Restore Higher TTLs

After 48 hours of stable behavior:

- Raise stable records to normal TTLs, for example `3600`.
- Raise Route 53 NS TTL to a normal value, for example `172800`.
- Keep volatile app/API records lower if frequent cutovers are expected.

Verification gate:

- No email failures.
- No app/API DNS failures.
- Provider callbacks healthy.
- Route 53 records match expected production state.

---

## 9. Rollback Plan

Rollback trigger examples:

- Company email cannot send or receive.
- `velvetelves.com` is unavailable and cannot be fixed quickly.
- `dev.velvetelves.com` breaks.
- Provider callbacks fail due DNS resolution.
- Wrong hosted zone or missing records are discovered after nameserver switch.

### 9.1 Fast Rollback

In GoDaddy:

1. Open Domain Portfolio.
2. Select `velvetelves.com`.
3. Open DNS / Nameservers.
4. Replace Route 53 nameservers with the previously recorded GoDaddy nameservers.
5. Save.

Then:

```powershell
Resolve-DnsName velvetelves.com -Type NS
Resolve-DnsName velvetelves.com -Type MX
Resolve-DnsName dev.velvetelves.com
```

### 9.2 After Rollback

1. Do not delete the Route 53 hosted zone.
2. Compare Route 53 records to the GoDaddy export.
3. Fix missing or incorrect records.
4. Wait for DNS to stabilize.
5. Schedule a second migration window.

Rollback is successful when:

- NS lookup returns GoDaddy nameservers again.
- Email works.
- Public sites resolve.
- `dev.velvetelves.com` works.

---

## 10. Phase F - Optional Registrar Transfer To Route 53

Goal: transfer domain registration from GoDaddy to Route 53 after Route 53 DNS hosting is stable.

Do not start this phase until:

- Route 53 has been authoritative for at least the agreed confidence window.
- Company email has been stable.
- Domain contact email is accessible.
- No app/API cutover is in progress.

### 10.1 Registrar Transfer Readiness

Confirm:

- `.com` transfer to Route 53 is supported.
- Domain is not within a 60-day transfer/registration/contact-change lock.
- Domain is unlocked in GoDaddy.
- DNSSEC is either disabled or intentionally planned.
- Domain privacy/contact behavior is understood.
- Registrant/admin email can receive transfer authorization emails.
- Payment method in AWS account is valid.
- Domain is not close to expiration.

### 10.2 Get GoDaddy Authorization Code

In GoDaddy:

1. Open Domain Portfolio.
2. Select `velvetelves.com`.
3. Choose transfer to another registrar.
4. Review the transfer checklist.
5. Continue and copy the authorization/EPP code.
6. Store it securely. Do not commit it.

### 10.3 Request Transfer In Route 53

In AWS Route 53 Domains:

1. Start domain transfer.
2. Enter `velvetelves.com`.
3. Enter the GoDaddy authorization code.
4. Choose contact privacy settings.
5. Confirm contact details.
6. Submit the transfer.
7. Approve required emails promptly.

Do not change DNS records during registrar transfer unless there is an emergency.

### 10.4 Monitor Transfer

Check:

- Route 53 domain transfer status.
- Registrant/admin email inbox.
- GoDaddy transfer status.
- Public DNS.
- Company email.

The transfer may take several days. Keep GoDaddy access until the transfer is complete and verified.

### 10.5 Post-Transfer

After completion:

1. Confirm Route 53 is the registrar.
2. Confirm Route 53 hosted zone remains authoritative.
3. Enable transfer lock in Route 53.
4. Confirm auto-renewal.
5. Confirm contact details.
6. Re-enable DNSSEC only if planned and tested.
7. Retain GoDaddy records export for audit history.

---

## 11. Final Acceptance Criteria

The migration is complete when:

- Route 53 is authoritative DNS for `velvetelves.com`.
- All expected public domains resolve correctly.
- `dev.velvetelves.com` is unchanged and healthy.
- Company email sends and receives successfully.
- SPF passes.
- DKIM passes.
- DMARC passes.
- Supabase, Google, Microsoft, Stripe, DocuSign, Gmail Pub/Sub, and Microsoft Graph callbacks are healthy.
- GoDaddy nameservers are no longer authoritative.
- The rollback nameserver list is archived.
- The Route 53 hosted zone is documented.
- Optional registrar transfer is either complete or explicitly deferred.

---

## 12. Do Not Do These Things

- Do not migrate DNS during an app/API production cutover.
- Do not transfer registrar ownership and DNS hosting at the same time.
- Do not edit email DNS records unless you know the email provider requirements.
- Do not delete the GoDaddy DNS export.
- Do not delete the Route 53 hosted zone during rollback.
- Do not enable DNSSEC until Route 53 DNS is stable and DNSSEC is deliberately planned.
- Do not terminate or repoint `dev.velvetelves.com` as part of this migration.
- Do not commit auth codes, provider verification tokens, or secret TXT values.

---

## 13. Official References

- AWS Route 53 DNS migration for a domain in use: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/migrate-dns-domain-in-use.html
- AWS Route 53 domain registration transfer: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-transfer-to-route-53.html
- AWS Route 53 supported TLDs: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/registrar-tld-list.html
- AWS Route 53 supported DNS record types: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/ResourceRecordTypes.html
- GoDaddy change nameservers: https://www.godaddy.com/help/change-nameservers-for-my-domains-664
- GoDaddy get authorization code for registrar transfer: https://www.godaddy.com/help/get-the-auth-code-for-my-domain-1685
