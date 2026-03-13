# Swagger UI Test Guide - Milestone 1.3 and 2.1

Last updated: 2026-03-10

## 1. Open Swagger UI

1. Start the backend:
```powershell
cd .\velvet-elves-backend
uvicorn app.main:app --reload
```
2. Open Swagger UI: `http://localhost:8000/api/docs`
3. Open OpenAPI JSON (optional): `http://localhost:8000/api/openapi.json`

Note: this project uses `/api/docs` (not `/docs`).

## 2. Auth Setup in Swagger (required for most endpoints)

1. Call `POST /api/v1/users/register` to create users for each role.
2. Call `POST /api/v1/users/login` to get an `access_token`.
3. Click `Authorize` in Swagger and paste `Bearer <access_token>`.

Important: `POST /api/v1/users/login` uses form fields (`username`, `password`), not JSON.

Useful enum values for tests:

- Roles: `Agent`, `Elf`, `TeamLead`, `Admin`, `Client`, `Vendor`
- Transaction use cases: `Buy-Fin`, `Buy-Cash`, `Sell-Fin`, `Sell-Cash`, `Both-Fin`, `Both-Cash`
- Transaction status: `Active`, `Incomplete`, `Paused`, `Completed`, `Closed`
- Contact types: `co_agent`, `loan_officer`, `title_rep`, `buyer`, `seller`, `inspector`, `appraiser`, `home_warranty`, `other`

---

## 3. Milestone 1.3 API Tests

Milestone 1.3 scope in this repo maps mainly to tags:

- `users`
- `invitations`
- `contacts`
- `vendors`
- `confidence`

### 3.1 Registration, Login, Profile, Password Reset

1. `POST /api/v1/users/register`
```json
{
  "email": "admin.m13@example.com",
  "password": "StrongPass1",
  "role": "Admin",
  "tenant_id": "tenant-m13"
}
```
Expected: `201` with token + user.
If Supabase email confirmation is enabled, you may get `202` with a confirmation message.

2. `POST /api/v1/users/login` (form-data)
- `username`: `admin.m13@example.com`
- `password`: `StrongPass1`

Expected: `200` with token + user.

3. `GET /api/v1/users/me` (after Authorize)
Expected: `200`.

4. `PATCH /api/v1/users/me`
```json
{
  "full_name": "Admin M13",
  "phone": "555-1111"
}
```
Expected: `200`.

5. `POST /api/v1/users/password-reset/request`
```json
{
  "email": "admin.m13@example.com"
}
```
Expected: `202`.

6. `POST /api/v1/users/password-reset/confirm`
```json
{
  "token": "auth-code-or-access-token",
  "new_password": "NewStrongPass1"
}
```
Expected: `200` if token is valid, otherwise `400`.

### 3.2 Invite-Based Onboarding

1. As `Agent`/`TeamLead`/`Admin`, call `POST /api/v1/invitations/`
```json
{
  "email": "new.elf@example.com",
  "role": "Elf"
}
```
Expected: `201`.

2. `GET /api/v1/invitations/`
Expected: `200`.

3. `GET /api/v1/invitations/verify/{token}`
Expected: `200` for valid token, `404`/`410` otherwise.

4. `POST /api/v1/invitations/accept/{token}`
```json
{
  "password": "InvitePass1",
  "full_name": "Invited Elf"
}
```
Expected: `201` (or `202` if email-confirmation flow is enabled), `404`/`410` for invalid or expired token.

Current implementation note: invitation emails send only when SMTP is configured. `POST /api/v1/invitations/` returns `email_sent` and `token` for verification/testing.

### 3.3 RBAC / Permission Middleware Checks

Run these negative tests to confirm RBAC:

1. Register/login a `Client`, then call `POST /api/v1/invitations/` -> expect `403`.
2. Register/login an `Agent`, then call `PUT /api/v1/confidence/tenant` -> expect `403`.
3. Register/login an `Agent`, create vendor, then `DELETE /api/v1/vendors/{id}` -> expect `403`.
4. Register/login an `Admin`, call same restricted endpoints -> expect success.

### 3.4 Contact Management API (CRUD + Search)

1. `POST /api/v1/contacts/`
```json
{
  "contact_type": "loan_officer",
  "full_name": "John Lender",
  "email": "john@bank.com",
  "phone": "555-0101",
  "company": "Big Bank"
}
```
Expected: `201`.

2. `GET /api/v1/contacts/` -> expect paginated list (`items`, `total`, `page`, `page_size`).
3. `GET /api/v1/contacts/search?q=john` -> expect matched list.
4. `GET /api/v1/contacts/{contact_id}` -> expect `200`.
5. `PATCH /api/v1/contacts/{contact_id}`
```json
{
  "full_name": "John Lender Jr",
  "phone": "555-9999"
}
```
Expected: `200`.

6. `DELETE /api/v1/contacts/{contact_id}` as `Agent`/`TeamLead`/`Admin` -> expect `204`.

### 3.5 Vendor Contact Card API

1. `POST /api/v1/vendors/`
```json
{
  "company_name": "ABC Title Co",
  "category": "title",
  "email": "info@abctitle.com"
}
```
Expected: `201`.

2. `GET /api/v1/vendors/{vendor_id}/contacts`
Expected: `200` (empty list is valid in current implementation).

Current implementation note: contact create/update schemas do not expose `vendor_id`, so linking contacts to a vendor card through Swagger alone is currently limited.

### 3.6 Confidence Threshold Settings API

1. As `Admin`, `PUT /api/v1/confidence/tenant`
```json
{
  "global_min_floor": 0.8,
  "auto_proceed_threshold": 0.95,
  "review_threshold": 0.8
}
```
Expected: `200`.

2. As `TeamLead` or `Admin`, `PUT /api/v1/confidence/team/{team_id}`
```json
{
  "global_min_floor": 0.85,
  "auto_proceed_threshold": 0.92
}
```
Expected: `200` if team floor is >= tenant floor, else `400`.

3. `GET /api/v1/confidence/` and `GET /api/v1/confidence/?team_id=...` -> verify effective settings.

---

## 4. Milestone 2.1 API Tests

Milestone 2.1 scope maps mainly to tags:

- `transactions`
- `transaction-assignments`

### 4.1 Transaction CRUD

1. `POST /api/v1/transactions`
```json
{
  "address": "456 Oak Avenue, Springfield, ST 12345",
  "use_case": "Buy-Fin",
  "purchase_price": 350000,
  "closing_date": "2026-09-30"
}
```
Expected: `201`.

2. `GET /api/v1/transactions` -> expect paginated result.
3. `GET /api/v1/transactions/{transaction_id}` -> expect `200`.
4. `PATCH /api/v1/transactions/{transaction_id}`
```json
{
  "status": "Paused"
}
```
Expected: `200`.

5. `DELETE /api/v1/transactions/{transaction_id}` as `TeamLead`/`Admin` -> expect `204`.
6. Try delete as `Agent` -> expect `403`.

### 4.2 Filtering, Sorting, Pagination

Test with query params on `GET /api/v1/transactions`:

- `status=Active`
- `use_case=Sell-Cash`
- `page=1&page_size=20`
- `sort_by=closing_date&sort_order=desc`
- `closing_date_from=2026-01-01&closing_date_to=2026-12-31`

Expected: `200` with filtered/sorted data.

Note: query `search` is in design docs but not exposed in current transactions route.

### 4.3 Status Management Endpoint

1. `PUT /api/v1/transactions/{transaction_id}/status`
```json
{
  "status": "Completed"
}
```
Expected: `200`.

2. Send invalid status:
```json
{
  "status": "NotAStatus"
}
```
Expected: `422`.

### 4.4 Transaction Type Switching

1. `PUT /api/v1/transactions/{transaction_id}/use-case`
```json
{
  "new_use_case": "Sell-Cash"
}
```
Expected: `200` with:

- `old_use_case`
- `new_use_case`
- `tasks_added`
- `tasks_removed`
- `tasks_preserved`

2. If new type equals old type, expect `200` with added/removed/preserved counters at `0`.

### 4.5 Transaction Assignment API

1. `POST /api/v1/transactions/{transaction_id}/assignments`
```json
{
  "user_id": "<use a real registered user id, for example an Elf user id>",
  "role_in_transaction": "Elf"
}
```
Expected: `201`.

2. `GET /api/v1/transactions/{transaction_id}/assignments` -> expect list.
3. `PATCH /api/v1/transactions/{transaction_id}/assignments/{assignment_id}`
```json
{
  "is_active": false
}
```
Expected: `200`.

4. `DELETE /api/v1/transactions/{transaction_id}/assignments/{assignment_id}`
- As `Agent` -> expect `403`
- As `TeamLead`/`Admin` -> expect `204`

### 4.6 Export API

1. `GET /api/v1/transactions/export/csv`
Expected: `200`, content-type includes `text/csv`.

2. `GET /api/v1/transactions/export/excel`
Expected: `200`, content-type includes spreadsheet MIME.

3. `GET /api/v1/transactions/export/pdf`
Expected: `200`, content-type `application/pdf`.

---

## 5. Minimal Regression Checklist (Quick Run)

1. Register + login one `Admin` and one `Agent`.
2. Authorize with `Admin` token and set tenant confidence.
3. Authorize with `Agent` token and create/list/update a contact.
4. Create a transaction, list it, change status, switch use-case.
5. Create/list/update assignment for that transaction.
6. Run CSV/PDF export endpoints.
7. Confirm at least one RBAC denial (`403`) with a low-privilege role.
