# Self-attestation draft (non-scannable AL1 items)

Draft for the lab packet. Facts below are as of 21 Aug 2026. Do not claim scans that were not run.

## Access control

- Tenant-scoped API: authenticated user must match tenant (and transaction where required). Platform admin is a separate console (`/api/v1/platform/*`).
- Google mailbox data is used only for the connected user of that integration row. There is no staff “open this customer’s Gmail” product.

## Key rotation

- `ENCRYPTION_KEY` (Fernet) and `SUPABASE_JWT_SECRET` live in AWS, not git. Rotation is a planned ops task; **no rotation drill is attached yet.**

## Backup encryption

- Supabase-managed Postgres; AWS-side backups follow the vendor defaults. **Attach vendor statements in the final packet; do not invent RPO numbers here.**

## Employee access to mailboxes

- Engineers with AWS/Supabase admin can theoretically decrypt `ENCRYPTION_KEY` and thus tokens. That is infra-admin access, not an in-app mailbox viewer. Product path: only the connected user (Settings → Disconnect).

## Deletion SLA

- Public pages: https://velvetelves.com/data-deletion and `/privacy`. Disconnect in Settings stops Google API calls (`is_active=false`). Stored Google-derived logs are deleted or anonymized **within 30 days** after a request to `support@velvetelves.com`, except legal/audit holds.
- Code does **not** currently null tokens on disconnect or delete the `integrations` row in tenant hard-delete. Do not tell the lab that Disconnect wipes ciphertext until that lands.

## Session cookies vs localStorage

- SPA session is localStorage JWT (not HttpOnly cookie). Compensating: HTTPS, CSP `connect-src` to the API, logout clears keys, Supabase JWT expiry. Full write-up: `compensating_controls.md`. Cookie migration is the preferred fix if the lab’s session-management CWE is a fail.

## OAuth popup

- Staging live 21 Aug 2026: callback pages `postMessage` only to `FRONTEND_URL` (`https://app.stage.velvetelves.com` on staging). SPA ignores other `event.origin` values. Browser smoke: Gmail + Calendar connect succeeded.

## AWS AI / OpenAI training

- AWS Organizations `AISERVICES_OPT_OUT_POLICY` enabled org-wide 20 Aug 2026 (includes Textract). OpenAI Sharing tab **captured 24 Aug 2026** (`openai-data-controls.png`): Velvetelves Organization, all three share radios Disabled. Do not claim ZDR from the Data retention tab.
