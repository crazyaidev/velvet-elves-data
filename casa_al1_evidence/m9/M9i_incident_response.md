# M9i — Incident response, retention, deletion

This is a **draft for the lab**, not a signed policy. Legal entity: Orange Door, LLP dba Velvet Elves (Indiana).

## Incident response (Google-user data)

If we learn of unauthorized access to Google user data (tokens, mailbox content we stored, or Gmail API abuse):

1. Contain: rotate `ENCRYPTION_KEY` only with a planned decrypt/re-encrypt; revoke Google grants via disconnect + user revoke at Google Account; rotate `X-VE-Cron-Secret` / app secrets if involved.
2. **Notify Google** of any Google-user-data incident (Google API Services User Data Policy). Use the Trust & Safety / Cloud Console incident channel Google documents for verified apps — do not invent a URL here; attach the current Google help article in the final packet.
3. Notify affected users at the account email. Support: `support@velvetelves.com`.
4. Preserve logs (CloudWatch + `request_id`) for the window. Do not paste tokens into tickets.

There is **no** separate IR ticket system documented in-repo. Until one exists, treat this as the operator checklist.

## Retention

- Workspace/transaction records: retained while the account is active (public privacy page).
- Gmail connection: used only while `integrations.is_active` is true.
- Communication logs: business records on the deal; not wiped by Disconnect alone (matches [data-deletion](https://velvetelves.com/data-deletion)).

## Deletion

Public pages (source of the 30-day number):

- https://velvetelves.com/privacy
- https://velvetelves.com/data-deletion (last updated 6 July 2026)

Product:

1. Settings → Integrations → Disconnect Gmail / Google Calendar → `is_active=false` (stops API calls immediately).
2. User may revoke at https://myaccount.google.com/connections
3. Deletion of **stored** Google-derived data: email `support@velvetelves.com`; target **30 days**, except legal/compliance/audit/transaction-record holds.

Code gaps to close before claiming a fully automated wipe:

- Disconnect does **not** null `access_token` / `refresh_token` on the row.
- `TenantDeletionService.DELETION_ORDER` does **not** list `integrations`.
- Tenant hard-delete runbook (`docs/runbooks/tenant_hard_delete.md`) still depends on a scheduled job; grace default in tests is ~30 days before hard delete.

## Backup encryption

Supabase-managed Postgres and AWS-side backups: vendor defaults. Attach current Supabase/AWS encryption statements in the paid packet. Do not invent RPO/RTO.
