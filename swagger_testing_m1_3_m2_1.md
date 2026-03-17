# Swagger UI Test Guide - Milestone 1.3 and 2.1

Last updated: 2026-03-17

Scope note: this guide now includes the current task template, task generation, task management, onboarding, integrations, documents, audit log, AI stub, and health-check routes currently exposed in Swagger UI.

## 1. Open Swagger UI

1. Start the backend:
```powershell
cd .\velvet-elves-backend
uvicorn app.main:app --reload
```
2. Open Swagger UI: `http://localhost:8000/api/docs`
3. Open OpenAPI JSON (optional): `http://localhost:8000/api/openapi.json`

Note: this project uses `/api/docs` (not `/docs`).

## 2. Auth Setup in Swagger

1. Call `POST /api/v1/users/register` to create a user.
2. Call `POST /api/v1/users/login` to get an `access_token`.
3. Click `Authorize` in Swagger and paste `Bearer <access_token>`.

Important auth notes:

- `POST /api/v1/users/login` uses form fields (`username`, `password`), not JSON.
- `POST /api/v1/users/confirm-email` and `POST /api/v1/users/password-reset/confirm` accept a `token` plus optional `refresh_token`.
- OAuth endpoints exist at `POST /api/v1/users/oauth/{provider}/start` and `POST /api/v1/users/oauth/{provider}/exchange` if Google or Microsoft login is configured.

Useful enum and query values for tests:

- Roles: `Agent`, `Elf`, `TeamLead`, `Admin`, `Client`, `Vendor`
- Transaction use cases: `Buy-Fin`, `Buy-Cash`, `Sell-Fin`, `Sell-Cash`, `Both-Fin`, `Both-Cash`
- Transaction status: `Active`, `Incomplete`, `Paused`, `Completed`, `Closed`
- Task status: `Pending`, `InProgress`, `Completed`, `Blocked`, `Skipped`
- Task automation levels: `Manual`, `Automated`, `AIAssisted`, `ToBeAutomated`
- Dependency relationship types: `FS`, `SS`
- Contact types: `co_agent`, `loan_officer`, `title_rep`, `buyer`, `seller`, `inspector`, `appraiser`, `home_warranty`, `other`
- Dashboard `view`: `personal`, `team`
- Dashboard card `filter`: `overdue`, `closing_soon`, `in_inspection`, `pending`
- Dashboard card `sort`: `urgency`, `closing_date`, `address`

---

## 3. Milestone 1.3 API Tests

Milestone 1.3 tags in this repo:

- `users`
- `invitations`
- `contacts`
- `vendors`
- `confidence`

### 3.1 Registration, Login, Confirm Email, Profile, Password Reset

1. `POST /api/v1/users/register`
```json
{
  "email": "admin.m13@example.com",
  "password": "StrongPass1",
  "full_name": "Admin M13",
  "phone": "555-1111",
  "role": "Admin",
  "tenant_id": "tenant-m13"
}
```
Expected: `201` with token + user. If Supabase email confirmation is enabled, you may get `202 Accepted` instead of an immediately usable session.

2. `POST /api/v1/users/login` (form-data)
- `username`: `admin.m13@example.com`
- `password`: `StrongPass1`

Expected: `200` with token + user.

3. `POST /api/v1/users/confirm-email` (only if email confirmation flow is enabled)
```json
{
  "token": "access-token-or-pkce-code",
  "refresh_token": "optional-refresh-token"
}
```
Expected: `200` with token + user, or `400` if the token or auth code is invalid.

4. `GET /api/v1/users/me`
Expected: `200`.

5. `PATCH /api/v1/users/me`
```json
{
  "full_name": "Admin M13 Updated",
  "phone": "555-2222"
}
```
Expected: `200`.

Current implementation note: the request schema exposes more profile fields, but `/users/me` currently persists `full_name` and `phone`.

6. `POST /api/v1/users/password-reset/request`
```json
{
  "email": "admin.m13@example.com",
  "redirect_to": "http://localhost:3000/reset-password"
}
```
Expected: `202` with a generic message whether or not the email exists.

7. `POST /api/v1/users/password-reset/confirm`
```json
{
  "token": "access-token-or-pkce-code",
  "refresh_token": "optional-refresh-token",
  "new_password": "NewStrongPass1"
}
```
Expected: `200` if the token is valid, otherwise `400`.

### 3.2 Optional OAuth Smoke Test

1. `POST /api/v1/users/oauth/google/start` or `POST /api/v1/users/oauth/microsoft/start`
```json
{
  "redirect_to": "http://localhost:3000/auth/callback",
  "scopes": "email profile"
}
```
Expected: `200` with `provider`, `url`, `state`, and `expires_in`.

2. `POST /api/v1/users/oauth/{provider}/exchange`
```json
{
  "code": "provider-auth-code",
  "state": "state-from-start-response"
}
```
Expected: `200` with token + user once OAuth is configured end-to-end.

### 3.3 Admin and Team Lead User Management

1. As `Admin` or `TeamLead`, call `GET /api/v1/users/`

Useful query params:

- `role=Agent`
- `team_id=<team uuid>`
- `is_active=true`
- `page=1&page_size=20`

Expected: `200` with `items`, `total`, `page`, and `page_size`.

Current implementation note: Team Leads are automatically scoped to their own `team_id` even if a different one is passed.

2. As `Admin`, call `GET /api/v1/users/{user_id}` -> expect `200`.

3. As `Admin`, call `PUT /api/v1/users/{user_id}/role`
```json
{
  "role": "Elf",
  "team_id": null
}
```
Expected: `200`.

4. As `Admin`, call `DELETE /api/v1/users/{user_id}` -> expect `200`.

Negative test: deleting your own user should return `400`.

### 3.4 Invite-Based Onboarding

1. As `Agent`, `TeamLead`, or `Admin`, call `POST /api/v1/invitations/`
```json
{
  "email": "new.elf@example.com",
  "role": "Elf",
  "team_id": null,
  "transaction_id": null
}
```
Expected: `201`.

2. `GET /api/v1/invitations/`
Expected: `200`.

3. `GET /api/v1/invitations/verify/{token}`
Expected: `200` for a valid token, `404` or `410` otherwise.

4. `POST /api/v1/invitations/accept/{token}`
```json
{
  "password": "InvitePass1",
  "full_name": "Invited Elf",
  "phone": "555-3333"
}
```
Expected: `201` with token + user, or `202` if the account still needs email confirmation.

5. As `TeamLead` or `Admin`, call `DELETE /api/v1/invitations/{invitation_id}` -> expect `204`.

Current implementation note: `POST /api/v1/invitations/` returns invitation metadata (`id`, `email`, `role`, `team_id`, `transaction_id`, `expires_at`, `is_used`). It no longer returns the raw invite token or `email_sent`.

### 3.5 RBAC and Permission Checks

Run a few negative tests to confirm role enforcement:

1. Register and log in a `Client`, then call `POST /api/v1/invitations/` -> expect `403`.
2. Register and log in an `Agent`, then call `PUT /api/v1/confidence/tenant` -> expect `403`.
3. Register and log in an `Agent`, create a vendor, then call `DELETE /api/v1/vendors/{vendor_id}` -> expect `403`.
4. Register and log in a `TeamLead`, then call `DELETE /api/v1/invitations/{invitation_id}` -> expect `204`.
5. Register and log in an `Admin`, then call the same restricted endpoints -> expect success where appropriate.

### 3.6 Contact Management API

1. `POST /api/v1/contacts/`
```json
{
  "contact_type": "loan_officer",
  "full_name": "John Lender",
  "email": "john@bank.com",
  "phone": "555-0101",
  "company": "Big Bank",
  "notes": "Primary financing contact",
  "is_vendor": false,
  "is_preferred": true,
  "state": "TX"
}
```
Expected: `201`.

2. `GET /api/v1/contacts/`

Useful query params:

- `contact_type=loan_officer`
- `is_vendor=false`
- `is_preferred=true`
- `vendor_id=<vendor uuid>`
- `page=1&page_size=20`

Expected: `200` with `items`, `total`, `page`, and `page_size`.

3. `GET /api/v1/contacts/search?q=john` -> expect a list of matching contacts.

4. `GET /api/v1/contacts/{contact_id}` -> expect `200`.

5. `PATCH /api/v1/contacts/{contact_id}`
```json
{
  "full_name": "John Lender Jr",
  "phone": "555-9999",
  "is_preferred": false
}
```
Expected: `200`.

6. `DELETE /api/v1/contacts/{contact_id}` as `Agent`, `TeamLead`, or `Admin` -> expect `204`.

### 3.7 Vendor API and Vendor Contact Card

1. `POST /api/v1/vendors/`
```json
{
  "company_name": "ABC Title Co",
  "category": "title",
  "website": "https://abctitle.example",
  "phone": "555-1212",
  "email": "info@abctitle.com",
  "address": "100 Main St, Springfield, ST 12345",
  "state": "ST",
  "notes": "Preferred local title partner",
  "is_preferred": true
}
```
Expected: `201`.

2. `GET /api/v1/vendors/`

Useful query params:

- `category=title`
- `is_preferred=true`
- `is_active=true`
- `page=1&page_size=20`

Expected: `200` with `items`, `total`, `page`, and `page_size`.

3. `GET /api/v1/vendors/{vendor_id}` -> expect `200`.

4. `PATCH /api/v1/vendors/{vendor_id}`
```json
{
  "notes": "Coverage expanded to neighboring counties",
  "is_preferred": false
}
```
Expected: `200`.

5. `GET /api/v1/vendors/{vendor_id}/contacts`
Expected: `200`.

6. To test the vendor contact card with real data, create a contact with `is_vendor: true` and `vendor_id: <vendor_id>`, then re-run `GET /api/v1/vendors/{vendor_id}/contacts`.

7. `DELETE /api/v1/vendors/{vendor_id}` as `TeamLead` or `Admin` -> expect `204`. As `Agent` -> expect `403`.

### 3.8 Confidence Threshold Settings API

1. As `Admin`, call `PUT /api/v1/confidence/tenant`
```json
{
  "global_min_floor": 0.8,
  "auto_proceed_threshold": 0.95,
  "review_threshold": 0.8,
  "task_overrides_json": {}
}
```
Expected: `200`.

2. As `TeamLead` or `Admin`, call `PUT /api/v1/confidence/team/{team_id}`
```json
{
  "global_min_floor": 0.85,
  "auto_proceed_threshold": 0.92
}
```
Expected: `200` if the team floor is greater than or equal to the tenant floor, otherwise `400`.

3. `GET /api/v1/confidence/`
Expected: `200`.

4. `GET /api/v1/confidence/?team_id=<team uuid>`
Expected: `200`.

Current implementation note: if nothing is configured yet, the endpoint returns defaults `global_min_floor=0.75`, `auto_proceed_threshold=0.90`, and `review_threshold=0.75`.

---

## 4. Milestone 2.1 API Tests

Milestone 2.1 and current tasking tags in this repo:

- `transactions`
- `task-templates`
- `tasks`
- `transaction-assignments`
- `transaction-parties`
- `dashboard`

### 4.1 Transaction CRUD

1. `POST /api/v1/transactions`
```json
{
  "address": "456 Oak Avenue, Springfield, ST 12345",
  "use_case": "Buy-Fin",
  "purchase_price": 350000,
  "closing_date": "2026-09-30",
  "status": "Active"
}
```
Expected: `201`.

2. `GET /api/v1/transactions`
Expected: `200` with `items`, `total`, `page`, `page_size`, and `pages`.

3. `GET /api/v1/transactions/{transaction_id}` -> expect `200`.

4. `PATCH /api/v1/transactions/{transaction_id}`
```json
{
  "city": "Springfield",
  "state": "ST",
  "zip_code": "12345",
  "county": "Example County",
  "financing_type": "Cash",
  "representation_type": "Buyer",
  "earnest_money": 5000,
  "contract_acceptance_date": "2026-08-01",
  "closing_date": "2026-09-15",
  "possession_date": "2026-09-16",
  "has_inspection": true,
  "inspection_days": 10,
  "inspection_response_days": 3,
  "has_hoa": false,
  "has_home_warranty": true,
  "warranty_ordered_by": "Buyer Agent",
  "title_ordered_by": "ABC Title Co",
  "insurance_commitment_days": 15,
  "is_owner_occupied": true,
  "notes": "Updated through Swagger"
}
```
Expected: `200`.

5. `DELETE /api/v1/transactions/{transaction_id}` as `TeamLead` or `Admin` -> expect `204`.
6. Try the same delete as `Agent` -> expect `403`.

Current implementation note: the create schema exposes many optional transaction fields, but the create route currently persists `address`, `use_case`, `purchase_price`, `closing_date`, and `status`. Use `PATCH /api/v1/transactions/{transaction_id}` to verify the richer field set end-to-end.

### 4.2 Filtering, Sorting, and Pagination

Test `GET /api/v1/transactions` with query params such as:

- `status=Active`
- `use_case=Sell-Cash`
- `state=ST`
- `financing_type=Cash`
- `representation_type=Buyer`
- `search=springfield`
- `page=1&page_size=20`
- `sort_by=closing_date&sort_order=desc`
- `sort_by=purchase_price&sort_order=asc`
- `closing_date_from=2026-01-01&closing_date_to=2026-12-31`

Expected: `200` with filtered and sorted data.

Supported `sort_by` values:

- `closing_date`
- `created_at`
- `updated_at`
- `purchase_price`
- `status`
- `use_case`
- `address`
- `state`
- `city`

Current implementation notes:

- Invalid `sort_by` values fall back to `closing_date`.
- `search`, `closing_date_from`, and `closing_date_to` are applied after the page query in the repository, so `items` reflect the filter but `total` and `pages` may still reflect the pre-search or pre-date-filter count.
- Admins and Team Leads list all tenant transactions. Agents and Elves are automatically scoped to their own transactions in the list endpoint.

### 4.3 Export API

1. `GET /api/v1/transactions/export/csv`

Optional query params:

- `status`
- `use_case`

Expected: `200`, content-type includes `text/csv`.

2. `GET /api/v1/transactions/export/excel`

Optional query params:

- `status`
- `use_case`

Expected: `200`, content-type includes `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.

3. `GET /api/v1/transactions/export/pdf`

Optional query params:

- `status`
- `use_case`

Expected: `200`, content-type `application/pdf`.

### 4.4 Status Management Endpoint

1. `PUT /api/v1/transactions/{transaction_id}/status`
```json
{
  "status": "Completed"
}
```
Expected: `200`.

2. Send an invalid status:
```json
{
  "status": "NotAStatus"
}
```
Expected: `422`.

### 4.5 Transaction Type Switching

1. `PUT /api/v1/transactions/{transaction_id}/use-case`
```json
{
  "new_use_case": "Sell-Cash"
}
```
Expected: `200` with:

- `transaction`
- `old_use_case`
- `new_use_case`
- `tasks_added`
- `tasks_removed`
- `tasks_preserved`

2. If the new type equals the old type, expect `200` with all counters at `0`.

Current implementation note: this endpoint now delegates the add/remove/preserve logic to the task generation service. It is most meaningful after the transaction already has tasks, ideally generated from the task-template library.

### 4.6 Task Template Library API

1. As `Admin` or `TeamLead`, call `POST /api/v1/task-templates`
```json
{
  "name": "Buyer Welcome",
  "description": "Send the buyer welcome message",
  "target": "Buyer",
  "cc_targets": ["Agent"],
  "milestone_label": "Buyer Welcomed",
  "use_cases": ["Buy-Fin", "Buy-Cash"],
  "dep_rel": "FS",
  "dep_task_id": 5,
  "float_days": "0",
  "automation_level": "Automated",
  "conditions_json": [],
  "both_rep_behavior": "skip",
  "category": "welcome",
  "sort_order": 10,
  "legacy_task_id": 10
}
```
Expected: `201` with fields such as `id`, `name`, `use_cases`, `target`, `automation_level`, and `is_active`.

2. `GET /api/v1/task-templates`

Useful query params:

- `use_case=Buy-Fin`
- `category=welcome`
- `automation_level=Automated`
- `search=buyer`
- `is_active=true`
- `page=1&page_size=20`

Expected: `200` with a list of templates visible to the current user.

3. `GET /api/v1/task-templates/by-use-case/Buy-Fin`
Expected: `200` with only active templates for that use case.

4. `GET /api/v1/task-templates/{template_id}` -> expect `200`.

5. `PUT /api/v1/task-templates/{template_id}`
```json
{
  "name": "Buyer Welcome Updated",
  "float_days": "5",
  "category": "onboarding"
}
```
Expected: `200`.

6. `DELETE /api/v1/task-templates/{template_id}` -> expect `204`.

7. After delete, call `GET /api/v1/task-templates/{template_id}` again and confirm `is_active` is now `false`.

Negative tests:

- As `Agent`, call `POST /api/v1/task-templates` -> expect `403`.
- If you have a system-wide template row or a template owned by another team, a `TeamLead` should get `403` when attempting to update or deactivate it.

Current implementation notes:

- `GET /api/v1/task-templates` accepts `page` and `page_size`, but the response is a plain array rather than a paginated envelope.
- The list route defaults to `is_active=true`. Use the direct `GET /api/v1/task-templates/{template_id}` route to verify a deactivated template still exists with `is_active=false`.

### 4.7 Task Generation from Templates

Recommended setup: create a few task templates for the transaction's `use_case`, then generate tasks on a fresh transaction with no existing tasks.

1. `POST /api/v1/transactions/{transaction_id}/tasks/generate`
Expected: `201` with:

- `tasks_generated`
- `transaction_id`

2. Verify the result with `GET /api/v1/tasks/transaction/{transaction_id}` and confirm the generated task names and metadata look correct.

3. Run `POST /api/v1/transactions/{transaction_id}/tasks/generate` again on the same transaction.
Expected: `409`.

4. Try the same endpoint with an invalid transaction id.
Expected: `404`.

Current implementation note: generation is rejected as soon as any tasks already exist for the transaction. Use a brand-new transaction for generation tests.

### 4.8 Task API

1. `POST /api/v1/tasks`
```json
{
  "name": "Order Title Work",
  "transaction_id": "<transaction_id>",
  "description": "Coordinate title opening",
  "target": "Title",
  "cc_targets": ["Agent", "Loan Officer"],
  "milestone_label": "Title Ordered",
  "due_date": "2026-08-05",
  "dep_rel": "FS",
  "dependencies": [],
  "automation_level": "Manual",
  "status": "Pending",
  "sort_order": 10,
  "template_id": null,
  "source": "manual"
}
```
Expected: `201`.

2. `GET /api/v1/tasks`

Useful query params:

- `status=Pending`
- `target=Title`
- `due_date_from=2026-01-01`
- `due_date_to=2026-12-31`
- `search=title`
- `sort_by=due_date&sort_order=asc`
- `sort_by=name&sort_order=desc`
- `page=1&page_size=20`

Expected: `200` with a list of tasks across accessible transactions.

3. `GET /api/v1/tasks/transaction/{transaction_id}`

Useful query params:

- `status=Pending`
- `target=Title`
- `sort_by=sort_order&sort_order=asc`

Expected: `200` with a list of tasks for that transaction.

4. `GET /api/v1/tasks/{task_id}` -> expect `200`.

5. `PATCH /api/v1/tasks/{task_id}`
```json
{
  "status": "Completed",
  "notes": "Completed in Swagger"
}
```
Expected: `200` with `status=Completed` and a non-null `completed_at`.

6. `PUT /api/v1/tasks/{task_id}/status`
```json
{
  "status": "InProgress"
}
```
Expected: `200`.

7. Send an invalid status to `PUT /api/v1/tasks/{task_id}/status`
```json
{
  "status": "NotAStatus"
}
```
Expected: `422`.

8. `GET /api/v1/tasks/vendor-carts`
Expected: `200` with items containing `vendor`, `tasks`, `total_count`, and `overdue_count`.

9. `GET /api/v1/tasks/summary`
Expected: `200` with `overdue`, `due_today`, `upcoming`, `completed`, and `total`.

10. `GET /api/v1/tasks/summary?transaction_id=<transaction_id>`
Expected: `200` with the same fields, scoped to one transaction.

11. `DELETE /api/v1/tasks/{task_id}`
- As `TeamLead` or `Admin` -> expect `204`
- As `Agent` or `Elf` -> expect `403`

Current implementation notes:

- Supported `sort_by` values for the task list routes are `due_date`, `status`, `name`, and `sort_order`.
- Invalid `sort_by` falls back to `due_date` on `GET /api/v1/tasks` and `sort_order` on `GET /api/v1/tasks/transaction/{transaction_id}`.
- Both task list endpoints accept `page` and `page_size`, but return plain arrays rather than paginated envelopes.
- Agents and Elves are scoped to tasks on their own transactions. Admins and Team Leads see tenant-scoped results.
- `GET /api/v1/tasks/vendor-carts` excludes tasks with status `Completed` or `Skipped`, and also excludes tasks without a `target`.
- In `GET /api/v1/tasks/summary`, the `completed` counter includes both `Completed` and `Skipped` tasks.
- The create schema exposes `notes`, but `POST /api/v1/tasks` does not currently persist it. Use `PATCH /api/v1/tasks/{task_id}` if you want to verify notes storage.

### 4.9 Transaction Assignment API

1. `POST /api/v1/transactions/{transaction_id}/assignments`
```json
{
  "user_id": "<use a real registered user id>",
  "role_in_transaction": "Elf"
}
```
Expected: `201`.

2. `GET /api/v1/transactions/{transaction_id}/assignments` -> expect `200` with a list.

3. `PATCH /api/v1/transactions/{transaction_id}/assignments/{assignment_id}`
```json
{
  "is_active": false,
  "role_in_transaction": "Backup Elf"
}
```
Expected: `200`.

4. `DELETE /api/v1/transactions/{transaction_id}/assignments/{assignment_id}`
- As `Agent` -> expect `403`
- As `TeamLead` or `Admin` -> expect `204`

Current implementation note: `role_in_transaction` is a free-form string, not a closed enum.

### 4.10 Transaction Parties API

Use these endpoints to manage external deal participants such as buyers, sellers, loan officers, title reps, inspectors, and appraisers.

1. `POST /api/v1/transactions/{transaction_id}/parties`
```json
{
  "party_role": "loan_officer",
  "contact_id": null,
  "full_name": "Jamie Lender",
  "email": "jamie@bank.com",
  "phone": "555-0202",
  "company": "Big Bank",
  "is_primary": true,
  "source": "manual"
}
```
Expected: `201` with `id`, `transaction_id`, `contact_id`, `party_role`, `full_name`, `email`, `phone`, `company`, `is_primary`, `source`, `created_at`, and `updated_at`.

2. `GET /api/v1/transactions/{transaction_id}/parties`
Expected: `200` with a plain array of transaction-party rows for that transaction.

3. `PUT /api/v1/transactions/{transaction_id}/parties/{party_id}`
```json
{
  "party_role": "title_rep",
  "full_name": "Jamie Lender",
  "email": "jamie@bank.com",
  "phone": "555-1111",
  "company": "Premier Title",
  "is_primary": false
}
```
Expected: `200`.

4. `DELETE /api/v1/transactions/{transaction_id}/parties/{party_id}`
- As `Elf` -> expect `403`
- As `Agent`, `TeamLead`, or `Admin` -> expect `204`

Current implementation notes:

- Common `party_role` examples from the schema/design are `buyer`, `seller`, `listing_agent`, `buyers_agent`, `loan_officer`, `title_rep`, `title_company`, `inspector`, `appraiser`, `home_warranty_company`, and `other`, but the API currently treats `party_role` as a free-form string.
- `contact_id` is optional. Use a real contact UUID if you want to verify contact-directory linkage; otherwise test with denormalized `full_name`, `email`, and `phone`.
- `POST` and `PUT` allow `Agent`, `Elf`, `TeamLead`, and `Admin`. `DELETE` allows `Agent`, `TeamLead`, and `Admin`. `GET` requires auth plus tenant access to the transaction.
- `PUT` behaves like a partial update in the current implementation: omitted fields stay unchanged even though the route uses `PUT`.
- Fields sent as `null` on `PUT` are ignored by the repository today, so this endpoint currently does not clear existing values.
- `source` is settable on create, but the update schema does not expose it.
- Expect `404` if the transaction does not exist, and `404` if the `party_id` does not belong to that transaction.

### 4.11 Dashboard Aggregation API

All dashboard endpoints require auth and read only transactions with status `Active`, `Incomplete`, or `Paused`.

Shared query params used across the dashboard routes:

- `view=personal|team`
- `team_member_id=<user id>` (mainly useful for `Admin` and `TeamLead`)
- For `GET /api/v1/dashboard/transaction-cards`: `filter`, `sort`, `search`, `page`, and `page_size`

Current implementation note: for `Admin` and `TeamLead`, `view=personal` behaves like full-tenant scope unless `team_member_id` is provided.

1. `GET /api/v1/dashboard/triage?view=personal`
Expected: `200` with `overdue`, `due_tomorrow`, `active_deals`, and `closing_soon`.

2. `GET /api/v1/dashboard/status-ribbon?view=personal`
Expected: `200` with `overdue_tasks`, `due_tomorrow`, `closing_this_month`, and `unread_messages`.

Current implementation note: `unread_messages` is currently `0`.

3. `GET /api/v1/dashboard/pipeline-summary?view=team`
Expected: `200` with:

- `closing_this_month`
- `in_inspection`
- `active_deals`
- `pending_contracts`
- `total_pipeline_value`

Each of the first four fields is a `PipelineCard` with `label`, `count`, and optional `subtitle`.

4. `GET /api/v1/dashboard/upcoming-closings?view=personal`
Expected: `200` with `items[]` containing:

- `transaction_id`
- `address`
- `closing_date`
- `days_remaining`
- `urgency_tier` (`urgent`, `soon`, `normal`)

5. `GET /api/v1/dashboard/needs-attention?view=personal`
Expected: `200` with `items[]` containing overdue or due-today tasks:

- `task_id`
- `task_name`
- `deal_name`
- `deal_id`
- `due_date`
- `is_overdue`

6. `GET /api/v1/dashboard/transaction-cards?view=personal&sort=urgency&page=1&page_size=20`

Useful extra query params:

- `filter=overdue`
- `filter=closing_soon`
- `filter=in_inspection`
- `filter=pending`
- `sort=closing_date`
- `sort=address`
- `search=springfield`

Expected: `200` with `items[]` plus `total`.

Key response fields per card:

- `transaction_id`
- `address`, `city`, `state`
- `use_case`, `status`
- `stage_pill`, `stage_pill_color`
- `purchase_price`, `closing_date`
- `next_deadline`, `next_deadline_label`
- `milestone_timeline`
- `inline_tasks`
- `contacts`
- `task_count`, `doc_count`, `message_count`

Current implementation notes:

- `contacts` comes from `transaction_parties`, not the general contacts directory.
- `doc_count` comes from the `documents` table.
- `client_name`, `assignee_name`, and `message_count` are currently unpopulated or zero-valued fields.
- Bare transactions with no tasks, documents, or transaction parties still return `200`, but many counts and arrays will be empty.

---

## 5. Additional Current Swagger UI APIs

These routes are currently exposed in Swagger UI even though they fall outside the original Milestone 1.3 / 2.1 grouping above.

Current additional Swagger tags/endpoints in this repo:

- `health`
- `onboarding`
- `integrations`
- `documents`
- `audit-logs`
- `ai`

### 5.1 Health Check

1. `GET /api/health`
Expected: `200` with `status`, `env`, and `version`.

Current implementation note: this route does not require auth and is included in Swagger as `/api/health`. The plain `/health` route exists too, but it is not included in the OpenAPI schema.

### 5.2 Onboarding API

1. `GET /api/v1/onboarding/status`
Expected: `200` with `message` and `onboarding_completed`.

2. `PATCH /api/v1/onboarding/company`
```json
{
  "company_name": "Velvet Elves Realty",
  "company_logo_url": "https://example.com/logo.png",
  "role": "Agent"
}
```
Expected: `200` with the refreshed user profile.

3. `POST /api/v1/onboarding/complete`
Expected: `200` with `message` and `onboarding_completed: true`.

Current implementation notes:

- `PATCH /api/v1/onboarding/company` requires at least one of `company_name`, `company_logo_url`, or `role`. Sending an empty body should return `400`.
- The company endpoint stores the logo URL only. The actual logo file upload is handled outside this route.
- `POST /api/v1/onboarding/complete` is idempotent, so calling it more than once should still return `200`.

### 5.3 Integrations API

These routes are currently stubbed for UI flow testing. They do not perform a real Google or Microsoft OAuth token exchange yet.

1. `GET /api/v1/integrations`
Expected: `200` with a list. A new account will usually return `[]`.

2. `POST /api/v1/integrations/connect`
```json
{
  "provider": "gmail",
  "auth_code": "stub-auth-code",
  "provider_email": "agent.integration@example.com"
}
```
Expected: `200` with `id`, `provider`, `provider_email`, `connected_at`, and `is_active`.

3. Repeat `POST /api/v1/integrations/connect` with `"provider": "outlook"` if you want to verify both supported providers.

4. `DELETE /api/v1/integrations/gmail`
Expected: `204` after a Gmail connection exists.

Negative checks:

- `POST /api/v1/integrations/connect` with `"provider": "yahoo"` -> expect `400`
- `DELETE /api/v1/integrations/gmail` before any Gmail connection exists -> expect `404`

Current implementation notes:

- Supported providers are only `gmail` and `outlook`.
- `auth_code` is optional right now and is not exchanged with the provider yet.
- Reconnecting the same provider updates or reactivates the existing row rather than creating a duplicate active connection.

### 5.4 Documents API

Use Swagger's file picker for the upload endpoint. This route uses `multipart/form-data`, not JSON.

1. `POST /api/v1/documents/upload`

Form fields:

- `file`: choose a small `.pdf`, `.docx`, `.doc`, `.jpg`, `.png`, `.webp`, or `.txt`
- `transaction_id`: optional; use a real transaction id if you want to verify transaction linkage

Expected: `201` with document metadata including `id`, `file_name`, `storage_path`, `mime_type`, `size_bytes`, `status`, `transaction_id`, and `created_at`.

2. `GET /api/v1/documents`
Expected: `200` with a list of documents uploaded by the current user.

3. `GET /api/v1/documents/{document_id}`
Expected: `200` for a document uploaded by the current user.

Negative checks:

- Upload an unsupported file type such as a CSV or executable -> expect `415`
- Upload a file larger than 20 MB -> expect `413`
- Request another user's `document_id` -> expect `404`

Current implementation notes:

- Documents are stored in the Supabase Storage bucket named `documents`, and metadata is recorded in the `documents` table.
- If storage upload fails because storage is not configured correctly, expect `502`.
- The list and single-document routes are scoped to the authenticated user's own uploads.

### 5.5 Audit Logs API

You will get the most meaningful results after exercising create, update, delete, role-change, or onboarding flows first so there are audit rows to inspect.

1. As `Admin`, call `GET /api/v1/audit-logs/`

Useful query params:

- `entity_type=transaction`
- `entity_id=<transaction_id>`
- `action=create`
- `user_id=<user_id>`
- `page=1&page_size=50`

Expected: `200` with `items`, `total`, `page`, and `page_size`.

2. As `Admin` or `TeamLead`, call `GET /api/v1/audit-logs/{entity_type}/{entity_id}`
Expected: `200` with a plain array of audit rows for that entity.

Negative checks:

- As `TeamLead`, call `GET /api/v1/audit-logs/` -> expect `403`
- As `Agent`, call `GET /api/v1/audit-logs/{entity_type}/{entity_id}` -> expect `403`

Current implementation notes:

- The tenant-wide list route is `Admin` only.
- The entity-specific route allows `Admin` and `TeamLead`.
- The list route currently supports `entity_type`, `entity_id`, `action`, `user_id`, `page`, and `page_size` query params.
- The entity-specific route is not paginated.

### 5.6 AI Stub API

These endpoints require auth but currently return stubbed AI-style responses rather than live OpenAI outputs.

1. `POST /api/v1/ai/parse`
```json
{
  "content": "Purchase agreement for 123 Main Street with a purchase price of 500000 and closing on 2026-07-15.",
  "document_type": "purchase_agreement"
}
```
Expected: `200` with `extracted`, `confidence`, and `needs_review`.

2. `POST /api/v1/ai/recommend-tasks`
```json
{
  "transaction_id": "<use a real transaction id or placeholder uuid>",
  "current_tasks": [
    {
      "name": "Send Welcome Email",
      "status": "Completed"
    }
  ]
}
```
Expected: `200` with `suggestions`, `confidence`, and `needs_review`.

Current implementation notes:

- `POST /api/v1/ai/parse` returns mocked extracted fields such as `address`, `purchase_price`, `closing_date`, `buyer_name`, `seller_name`, and `earnest_money`.
- `POST /api/v1/ai/recommend-tasks` returns mocked task suggestions, so do not expect transaction-specific recommendations yet.
- `needs_review` depends on the configured AI confidence threshold.

---

## 6. Minimal Regression Checklist

1. Register and log in an `Admin`, a `TeamLead`, an `Agent`, and an `Elf`.
2. As `Admin`, set tenant confidence and optionally smoke-test `GET /api/v1/users/`.
3. As `Agent`, create a contact, create a vendor, and create a vendor-linked contact using `vendor_id`.
4. As `Admin` or `TeamLead`, create a few task templates for one use case and verify create, list, by-use-case, get, update, and deactivate behavior.
5. Create a fresh transaction, patch richer fields onto it, list it with filters, and generate tasks from templates.
6. Exercise the task endpoints: list all tasks, list transaction tasks, patch a task to `Completed`, hit `PUT /api/v1/tasks/{task_id}/status`, then call `/tasks/vendor-carts` and `/tasks/summary`.
7. Switch the transaction use-case and verify `tasks_added`, `tasks_removed`, and `tasks_preserved`.
8. Create at least one transaction assignment for that transaction and verify list, update, and delete behavior by role.
9. Create at least one transaction party for that transaction and verify create, list, update, and delete behavior by role.
10. Call the dashboard endpoints. Expect the richest responses only if you already have related tasks, documents, and transaction-party rows.
11. Run CSV, Excel, and PDF transaction exports.
12. Confirm at least one `403` with a low-privilege role, one `404` using an invalid resource id, and one `409` by re-running task generation on the same transaction.
13. Smoke-test the remaining Swagger-visible routes: `GET /api/health`, onboarding status/company/complete, integrations list/connect/disconnect, documents upload/list/get, audit log list/entity lookup, and AI parse/recommend.
