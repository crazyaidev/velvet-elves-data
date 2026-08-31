# M9e — PII encryption

`app/utils/encryption.py` + `SYSTEM_DESIGN.md` (if present in the backend repo).

Fields encrypted at rest with the same Fernet key as Google tokens include integration emails/tokens and selected party PII (`transaction_party_repository`: name, email, phone).

This is application-layer encryption in addition to Supabase/Postgres storage encryption. It is **not** end-to-end encryption from the browser; the API decrypts to process Gmail/Calendar calls.
