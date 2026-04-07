# Swagger UI Test Guide - Current Backend API Coverage

Last updated: 2026-04-07

This file now tracks the current Swagger-visible backend surface, not just the original Milestone 1.3 / 2.1 routes. It is aligned to the routers registered in `velvet-elves-backend/app/api/v1/router.py` plus the health routes exposed from `app/main.py`.

Current Swagger tags:

- `health`
- `users`
- `invitations`
- `onboarding`
- `integrations`
- `documents`
- `transactions`
- `tasks`
- `task-templates`
- `contacts`
- `vendors`
- `confidence`
- `audit-logs`
- `transaction-assignments`
- `transaction-parties`
- `dashboard`
- `ai`
- `ai-settings`
- `teams`
- `tenants`
- `communication-logs`
- `notifications`

## 1. Open Swagger UI

1. Start the backend:

```powershell
cd .\velvet-elves-backend
uvicorn app.main:app --reload
```

2. Open Swagger UI: `http://localhost:8000/api/docs`
3. Open OpenAPI JSON if needed: `http://localhost:8000/api/openapi.json`

Notes:

- This project uses `/api/docs`, not `/docs`.
- Health routes are exposed in Swagger at `/api/health`, `/api/v1/health`, and `/api/v1/health/ready`.

## 2. Auth Setup in Swagger

If your local environment already has usable users, you can skip straight to login. Otherwise:

1. Call `POST /api/v1/users/register`

```json
{
  "email": "admin.swagger@example.com",
  "password": "StrongPass1",
  "full_name": "Swagger Admin",
  "phone": "555-0100",
  "role": "Admin",
  "tenant_id": "tenant-swagger"
}
```

If your environment requires a real tenant id, replace `tenant-swagger` with one that exists locally.

2. Call `POST /api/v1/users/login`

Important: Swagger shows this route as form fields, not JSON.

- `username`: `admin.swagger@example.com`
- `password`: `StrongPass1`

3. Copy the `access_token`.
4. Click `Authorize` in Swagger and paste `Bearer <access_token>`.

Suggested extra users for role testing:

- `Admin`
- `TeamLead`
- `Agent`
- `Elf`
- `Client`

Useful ids to keep handy while testing:

- `<tenant_id>`
- `<team_id>`
- `<team_lead_user_id>`
- `<agent_user_id>`
- `<transaction_id>`
- `<template_id>`
- `<task_id>`
- `<contact_id>`
- `<vendor_id>`
- `<document_id>`
- `<assignment_id>`
- `<party_id>`
- `<log_id>`

## 3. Shared Enums and Common Values

Roles:

- `Agent`
- `Elf`
- `TeamLead`
- `Attorney`
- `Admin`
- `Client`
- `FSBO_Customer`
- `Vendor`

Transaction use cases:

- `Buy-Fin`
- `Buy-Cash`
- `Sell-Fin`
- `Sell-Cash`
- `Both-Fin`
- `Both-Cash`

Transaction statuses:

- `Active`
- `Incomplete`
- `Paused`
- `Completed`
- `Closed`

Task statuses:

- `Pending`
- `InProgress`
- `Completed`
- `Blocked`
- `Skipped`

Task automation levels:

- `Manual`
- `Automated`
- `AIAssisted`
- `ToBeAutomated`

Dependency relationship types:

- `FS`
- `SS`

Closing modes:

- `attorney`
- `title_escrow`
- `shared_approval`

Contact types:

- `co_agent`
- `loan_officer`
- `title_rep`
- `attorney`
- `buyer`
- `seller`
- `inspector`
- `appraiser`
- `home_warranty`
- `other`

Communication channels:

- `email`
- `sms`
- `voice_call`
- `push`
- `system`
- `ai_draft`
- `note`
- `document_action`

Communication directions:

- `inbound`
- `outbound`
- `internal`

Document types:

- `purchase_agreement`
- `counter_offer`
- `amendment`
- `pre_approval`
- `title_work`
- `inspection_report`
- `hoa_docs`
- `closing_disclosure`
- `utility_info`
- `sellers_disclosure`
- `blc_tax_sheet`
- `earnest_money`
- `home_warranty`
- `insurance`
- `other`

AI providers:

- `openai`
- `anthropic`

Dashboard `view` values:

- `personal`
- `team`

Dashboard `tab` values for `GET /api/v1/dashboard/transaction-cards`:

- `all`
- `overdue`
- `today`
- `closing_soon`
- `in_inspection`
- `on_track`
- `unhealthy`

Dashboard `sort` values for `GET /api/v1/dashboard/transaction-cards`:

- `urgency`
- `close_date`
- `client_name`
- `price`

## 4. Recommended Test Data Order

Use this order if you want one pass through Swagger that sets up reusable data:

1. Register and log in an `Admin`.
2. Create or identify additional users for `TeamLead`, `Agent`, and `Elf`.
3. Create a team and add members.
4. Create a transaction with rich field data.
5. Create contacts and at least one vendor.
6. Create task templates, then generate tasks for the transaction.
7. Add transaction assignments and transaction parties.
8. Upload a document tied to the transaction.
9. Create a communication log tied to the transaction.
10. Run dashboard, notifications, audit, document, and AI flows against the data above.

## 5. Health APIs

1. `GET /api/health`
Expected: `200` with `status`, `env`, and `version`.

2. `GET /api/v1/health`
Expected: `200` with the same payload as `/api/health`.

3. `GET /api/v1/health/ready`
Expected: `200` with `status: "ready"` and `db: true` when the database is reachable.
Possible failure mode: `503` with `status: "unavailable"` if the DB connection is not ready.

## 6. Users APIs

### 6.1 Registration, Login, Confirm Email, and Password Reset

1. `POST /api/v1/users/register`

```json
{
  "email": "agent.swagger@example.com",
  "password": "StrongPass1",
  "full_name": "Swagger Agent",
  "phone": "555-0101",
  "role": "Agent",
  "tenant_id": "tenant-swagger"
}
```

Expected: `201` with token plus user in environments without deferred email confirmation.

2. `POST /api/v1/users/login`

Swagger form fields:

- `username`: `agent.swagger@example.com`
- `password`: `StrongPass1`

Expected: `200`.

3. `POST /api/v1/users/confirm-email`

```json
{
  "token": "access-token-or-pkce-code",
  "refresh_token": "optional-refresh-token"
}
```

Expected: `200` when the token is valid.

4. `POST /api/v1/users/password-reset/request`

```json
{
  "email": "agent.swagger@example.com",
  "redirect_to": "http://localhost:3000/reset-password"
}
```

Expected: `202`.

5. `POST /api/v1/users/password-reset/confirm`

```json
{
  "token": "access-token-or-pkce-code",
  "refresh_token": "optional-refresh-token",
  "new_password": "NewStrongPass1"
}
```

Expected: `200` when the token is valid.

### 6.2 Profile APIs

1. `GET /api/v1/users/me`
Expected: `200`.

2. `PATCH /api/v1/users/me`

```json
{
  "full_name": "Swagger Agent Updated",
  "phone": "555-1111"
}
```

Expected: `200`.

### 6.3 OAuth Smoke Tests

Use these only if Google or Microsoft OAuth is configured in your environment.

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

Expected: `200` when provider auth is wired end to end.

### 6.4 User Management APIs

Use an `Admin` or `TeamLead` token for list and lookup, and an `Admin` token for role changes and deletes.

1. `GET /api/v1/users/`

Useful query params:

- `role=Agent`
- `team_id=<team_id>`
- `is_active=true`
- `page=1&page_size=20`

Expected: `200` with `items`, `total`, `page`, and `page_size`.

2. `GET /api/v1/users/{user_id}`
Expected: `200`.

3. `PUT /api/v1/users/{user_id}/role`

```json
{
  "role": "Elf",
  "team_id": null
}
```

Expected: `200`.

4. `DELETE /api/v1/users/{user_id}`
Expected: `200`.
Negative check: deleting your own user should return `400`.

## 7. Invitations APIs

1. `POST /api/v1/invitations/`

```json
{
  "email": "new.elf.swagger@example.com",
  "role": "Elf",
  "team_id": null,
  "transaction_id": null
}
```

Expected: `201`.

2. `GET /api/v1/invitations/`
Expected: `200`.

3. `GET /api/v1/invitations/verify/{token}`
Expected: `200` for a valid token, otherwise `404` or `410`.

4. `POST /api/v1/invitations/accept/{token}`

```json
{
  "password": "InvitePass1",
  "full_name": "Invited Elf",
  "phone": "555-3333"
}
```

Expected: `201`.

5. `DELETE /api/v1/invitations/{invitation_id}`
Expected: `204`.

## 8. Onboarding APIs

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

Expected: `200`.

3. `POST /api/v1/onboarding/complete`
Expected: `200` with `onboarding_completed: true`.

## 9. Integrations APIs

These are currently suitable for UI flow testing rather than a real provider token exchange.

1. `GET /api/v1/integrations`
Expected: `200` with a list.

2. `POST /api/v1/integrations/connect`

```json
{
  "provider": "gmail",
  "auth_code": "stub-auth-code",
  "provider_email": "agent.integration@example.com"
}
```

Expected: `200`.

3. `POST /api/v1/integrations/connect` again with `"provider": "outlook"` to verify both supported providers.

4. `DELETE /api/v1/integrations/gmail`
Expected: `204` after a Gmail connection exists.

Negative checks:

- Use `"provider": "yahoo"` on connect and expect `400`
- Delete a provider that was never connected and expect `404`

## 10. Tenants APIs

These routes are `Admin` focused. `GET /api/v1/tenants/current` works for any authenticated user.

1. `POST /api/v1/tenants`

```json
{
  "name": "Swagger Realty",
  "slug": "swagger-realty",
  "domain": "swagger.example.com",
  "logo_url": "https://example.com/swagger-logo.png",
  "primary_color": "#0f766e",
  "secondary_color": "#f59e0b",
  "settings_json": {
    "timezone": "America/Chicago"
  }
}
```

Expected: `201`.

2. `GET /api/v1/tenants`

Useful query params:

- `is_active=true`
- `page=1&page_size=20`

Expected: `200` with `items`, `total`, `page`, and `page_size`.

3. `GET /api/v1/tenants/current`
Expected: `200`.

4. `GET /api/v1/tenants/{tenant_id}`
Expected: `200`.

5. `PUT /api/v1/tenants/{tenant_id}`

```json
{
  "domain": "swagger-updated.example.com",
  "primary_color": "#1d4ed8",
  "secondary_color": "#f97316",
  "settings_json": {
    "timezone": "America/Denver",
    "feature_flag": true
  }
}
```

Expected: `200`.

6. `DELETE /api/v1/tenants/{tenant_id}`
Expected: `204`.
Negative check: attempting to deactivate your own tenant should return `400`.

## 11. Teams APIs

Use an `Admin` token for create, update, and delete. `Admin` and `TeamLead` can list, get, and manage membership.

1. `POST /api/v1/teams`

```json
{
  "name": "North Team",
  "lead_user_id": "<team_lead_user_id>",
  "settings_json": {
    "region": "north"
  }
}
```

Expected: `201`.

2. `GET /api/v1/teams`

Useful query params:

- `page=1&page_size=20`

Expected: `200` with `items`, `total`, `page`, and `page_size`.

3. `GET /api/v1/teams/{team_id}`
Expected: `200`.

4. `PUT /api/v1/teams/{team_id}`

```json
{
  "name": "North Team Updated",
  "settings_json": {
    "region": "north",
    "priority": "high"
  }
}
```

Expected: `200`.

5. `POST /api/v1/teams/{team_id}/members`

```json
{
  "user_id": "<agent_user_id>"
}
```

Expected: `200` with the updated user row.

6. `DELETE /api/v1/teams/{team_id}/members/{user_id}`
Expected: `204`.

7. `DELETE /api/v1/teams/{team_id}`
Expected: `204`.

Negative check: a `TeamLead` should only be able to manage membership for their own team.

## 12. Contacts APIs

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
- `vendor_id=<vendor_id>`
- `page=1&page_size=20`

Expected: `200` with `items`, `total`, `page`, and `page_size`.

3. `GET /api/v1/contacts/search?q=john`
Expected: `200` with matching contacts.

4. `GET /api/v1/contacts/{contact_id}`
Expected: `200`.

5. `PATCH /api/v1/contacts/{contact_id}`

```json
{
  "full_name": "John Lender Jr",
  "phone": "555-9999",
  "is_preferred": false
}
```

Expected: `200`.

6. `DELETE /api/v1/contacts/{contact_id}`
Expected: `204`.

## 13. Vendors APIs

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

3. `GET /api/v1/vendors/{vendor_id}`
Expected: `200`.

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

6. Create a vendor-linked contact by setting `is_vendor: true` and `vendor_id: <vendor_id>`, then repeat `GET /api/v1/vendors/{vendor_id}/contacts`.

7. `DELETE /api/v1/vendors/{vendor_id}`
Expected: `204` for authorized roles.

## 14. Confidence APIs

1. `GET /api/v1/confidence/`
Expected: `200`.

2. `PUT /api/v1/confidence/tenant`

```json
{
  "global_min_floor": 0.8,
  "auto_proceed_threshold": 0.95,
  "review_threshold": 0.8,
  "task_overrides_json": {}
}
```

Expected: `200`.

3. `PUT /api/v1/confidence/team/{team_id}`

```json
{
  "global_min_floor": 0.85,
  "auto_proceed_threshold": 0.92
}
```

Expected: `200`.

4. `GET /api/v1/confidence/?team_id=<team_id>`
Expected: `200`.

## 15. Transactions APIs

Use one rich transaction payload so the rest of the guide has realistic data to work with.

1. `POST /api/v1/transactions`

```json
{
  "address": "456 Oak Avenue, Springfield, ST 12345",
  "city": "Springfield",
  "state": "ST",
  "zip_code": "12345",
  "county": "Example County",
  "use_case": "Buy-Fin",
  "financing_type": "Financed",
  "representation_type": "Buyer",
  "purchase_price": 350000,
  "earnest_money": 5000,
  "contract_acceptance_date": "2026-08-01",
  "closing_date": "2026-09-15",
  "closing_time": "14:00:00",
  "possession_date": "2026-09-16",
  "possession_time": "12:00:00",
  "em_delivered_date": "2026-08-03",
  "inspection_response_date": "2026-08-10",
  "appraisal_expected_date": "2026-08-20",
  "cd_delivered_date": "2026-09-12",
  "cleared_to_close_date": "2026-09-14",
  "has_inspection": true,
  "inspection_days": 10,
  "inspection_response_days": 3,
  "has_hoa": false,
  "has_home_warranty": true,
  "warranty_ordered_by": "Buyer Agent",
  "title_ordered_by": "ABC Title Co",
  "insurance_commitment_days": 15,
  "closing_mode": "title_escrow",
  "is_owner_occupied": true,
  "is_fsbo": false,
  "status": "Active",
  "notes": "Created through Swagger"
}
```

Expected: `201`.

2. `GET /api/v1/transactions`

Useful query params:

- `status=Active`
- `use_case=Buy-Fin`
- `state=ST`
- `financing_type=Financed`
- `representation_type=Buyer`
- `search=springfield`
- `page=1&page_size=20`
- `sort_by=closing_date&sort_order=desc`
- `sort_by=purchase_price&sort_order=asc`
- `closing_date_from=2026-01-01&closing_date_to=2026-12-31`

Expected: `200` with `items`, `total`, `page`, `page_size`, and `pages`.

3. `GET /api/v1/transactions/export/csv`
Expected: `200` with CSV content.

4. `GET /api/v1/transactions/export/excel`
Expected: `200` with XLSX content.

5. `GET /api/v1/transactions/export/pdf`
Expected: `200` with PDF content.

6. `GET /api/v1/transactions/{transaction_id}`
Expected: `200`.

7. `PATCH /api/v1/transactions/{transaction_id}`

```json
{
  "notes": "Patched through Swagger",
  "has_hoa": true,
  "hoa_doc_days": 5,
  "insurance_commitment_days": 18
}
```

Expected: `200`.

8. `PUT /api/v1/transactions/{transaction_id}/status`

```json
{
  "status": "Paused"
}
```

Expected: `200`.

9. `PUT /api/v1/transactions/{transaction_id}/key-dates`

```json
{
  "inspection_response_date": "2026-08-11",
  "closing_date": "2026-09-18",
  "closing_time": "15:30:00",
  "possession_date": "2026-09-19",
  "possession_time": "11:00:00"
}
```

Expected: `200`.

10. `PUT /api/v1/transactions/{transaction_id}/use-case`

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

11. `POST /api/v1/transactions/{transaction_id}/tasks/generate`
Expected: `201` with `tasks_generated` and `transaction_id`.
Important: this works best on a fresh transaction that does not already have tasks.

12. `GET /api/v1/transactions/{transaction_id}/history`
Expected: `200` with grouped timeline events. This becomes more useful after task updates, communication log entries, audit rows, and AI calls exist.

Useful query param:

- `search=closing`

13. `DELETE /api/v1/transactions/{transaction_id}`
Expected: `204` for `Admin` or `TeamLead`.

## 16. Task Templates APIs

1. `POST /api/v1/task-templates`

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

Expected: `201`.

2. `GET /api/v1/task-templates`

Useful query params:

- `use_case=Buy-Fin`
- `category=welcome`
- `automation_level=Automated`
- `search=buyer`
- `is_active=true`
- `page=1&page_size=20`

Expected: `200` with an array.

3. `GET /api/v1/task-templates/by-use-case/Buy-Fin`
Expected: `200`.

4. `GET /api/v1/task-templates/{template_id}`
Expected: `200`.

5. `PUT /api/v1/task-templates/{template_id}`

```json
{
  "name": "Buyer Welcome Updated",
  "float_days": "5",
  "category": "onboarding"
}
```

Expected: `200`.

6. `DELETE /api/v1/task-templates/{template_id}`
Expected: `204`.

7. `POST /api/v1/task-templates/import`

Use Swagger file upload with a `.csv` file.

Sample CSV:

```csv
Task Name,Task ID,Use Case,Target,CC:,Milestone Task,Deprel,Task Dependent,Float,Development Notes,Additional Notes,Task Description
Send Welcome Email,10,Buy-Fin,Buyer,Agent,Buyer Welcomed,FS,,0,,,Send the buyer welcome email
```

Expected: `201` with `imported`, `skipped`, and `errors`.

Negative check: upload a non-CSV file and expect `415`.

## 17. Tasks APIs

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

Expected: `200` with an array.

3. `GET /api/v1/tasks/transaction/{transaction_id}`

Useful query params:

- `status=Pending`
- `target=Title`
- `sort_by=sort_order&sort_order=asc`

Expected: `200`.

4. `GET /api/v1/tasks/vendor-carts`
Expected: `200` with grouped carts by `vendor`.

5. `GET /api/v1/tasks/summary`
Expected: `200` with `overdue`, `due_today`, `upcoming`, `completed`, and `total`.

6. `GET /api/v1/tasks/summary?transaction_id=<transaction_id>`
Expected: `200` scoped to one transaction.

7. `GET /api/v1/tasks/{task_id}`
Expected: `200`.

8. `PATCH /api/v1/tasks/{task_id}`

```json
{
  "status": "Completed",
  "notes": "Completed in Swagger"
}
```

Expected: `200`.

9. `PUT /api/v1/tasks/{task_id}/status`

```json
{
  "status": "InProgress",
  "notes": "Started from Swagger"
}
```

Expected: `200`.

10. `POST /api/v1/tasks/similar`

```json
{
  "transaction_id": "<transaction_id>",
  "name": "Order title commitment"
}
```

Expected: `200` with up to five similar incomplete tasks and `similarity` scores.

11. `GET /api/v1/tasks/transaction/{transaction_id}/closing-checklist`
Expected: `200` with `transaction_id`, `address`, `closing_date`, `total_tasks`, `completed_tasks`, and `items`.

12. `DELETE /api/v1/tasks/{task_id}`
Expected: `204` for `TeamLead` or `Admin`.

## 18. Transaction Assignments APIs

1. `POST /api/v1/transactions/{transaction_id}/assignments`

```json
{
  "user_id": "<agent_user_id>",
  "role_in_transaction": "Elf"
}
```

Expected: `201`.

2. `GET /api/v1/transactions/{transaction_id}/assignments`
Expected: `200`.

3. `PATCH /api/v1/transactions/{transaction_id}/assignments/{assignment_id}`

```json
{
  "is_active": false,
  "role_in_transaction": "Backup Elf"
}
```

Expected: `200`.

4. `DELETE /api/v1/transactions/{transaction_id}/assignments/{assignment_id}`
Expected: `204` for authorized roles.

## 19. Transaction Parties APIs

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

Expected: `201`.

2. `GET /api/v1/transactions/{transaction_id}/parties`
Expected: `200`.

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
Expected: `204` for authorized roles.

## 20. Dashboard APIs

These endpoints are now the current dashboard surface in Swagger UI. They replace the older triage and ribbon routes that no longer exist.

Shared query params:

- `view=personal|team`
- `team_member_id=<user_id>` for team-oriented admin or lead testing

1. `GET /api/v1/dashboard/ai-briefing?view=personal`
Expected: `200` with `critical_count`, `needs_attention_count`, `on_track_count`, and optional `suggested_focus`.

2. `GET /api/v1/dashboard/sidebar-kpis?view=personal`
Expected: `200` with `overdue_tasks`, `closing_this_week`, `active_deals`, and `pipeline_value`.

3. `GET /api/v1/dashboard/deal-state-counts?view=team`
Expected: `200` with `active_transactions`, `pending`, `closed`, and `all_transactions`.

4. `GET /api/v1/dashboard/transaction-cards?view=personal&tab=all&sort=urgency&page=1&page_size=20`

Useful extra query params:

- `tab=overdue`
- `tab=today`
- `tab=closing_soon`
- `tab=in_inspection`
- `tab=on_track`
- `tab=unhealthy`
- `sort=close_date`
- `sort=client_name`
- `sort=price`
- `search=springfield`

Expected: `200` with `items` and `total`.

Key card fields to spot check:

- `transaction_id`
- `address`, `city`, `state`, `zip_code`
- `client_name`, `assignee_name`
- `use_case`, `status`
- `stage_pill`, `stage_pill_color`
- `why_badges`
- `ai_next_step`
- `purchase_price`, `closing_date`, `days_to_close`
- `next_deadline`, `next_deadline_label`, `next_step_cta`
- `milestone_timeline`
- `inline_tasks`
- `task_sections`
- `contacts`
- `contact_groups`
- `key_dates`
- `task_count`, `doc_count`, `message_count`

5. `POST /api/v1/dashboard/ai-chat`

```json
{
  "message": "What should I work on next?",
  "transaction_id": "<transaction_id>"
}
```

Expected: `200` with `response` and `suggested_actions`.
Current behavior note: this endpoint still returns placeholder AI chat text.

## 21. Notifications APIs

1. `GET /api/v1/notifications/pending`

Optional query param:

- `days_ahead=3`

Expected: `200` with:

- `overdue`
- `due_today`
- `day_before`
- `upcoming`
- `transaction_summaries`
- `compiled_summary`

2. `POST /api/v1/notifications/daily-summary/trigger`
Expected: `200` with `summaries_queued` and `tenant_id`.
Role note: this route is `Admin` only.

## 22. Documents APIs

Use Swagger's file picker for upload and import-style routes.

1. `POST /api/v1/documents/upload`

Form fields:

- `file`: choose a `.pdf`, `.docx`, `.doc`, `.jpg`, `.png`, `.webp`, `.gif`, or `.txt`
- `transaction_id`: optional, but use a real transaction id for richer downstream tests
- `doc_type`: optional, example `purchase_agreement`
- `doc_label`: optional, example `Buyer Contract`

Expected: `201`.

2. `GET /api/v1/documents`

Useful query params:

- `transaction_id=<transaction_id>`
- `doc_type=purchase_agreement`
- `is_deleted=false`
- `search=contract`
- `page=1&page_size=20`

Expected: `200` with `items`, `total`, `page`, and `page_size`.

3. `GET /api/v1/documents/transaction/{transaction_id}`
Expected: `200` with an array of transaction documents.

4. `GET /api/v1/documents/{document_id}`
Expected: `200`.

5. `GET /api/v1/documents/{document_id}/download`
Expected: `200` with `download_url`, `file_name`, `mime_type`, and `expires_in`.

6. `PATCH /api/v1/documents/{document_id}`

```json
{
  "file_name": "renamed_contract.pdf",
  "doc_type": "purchase_agreement",
  "doc_label": "Buyer Contract Updated",
  "metadata_json": {
    "source": "swagger"
  }
}
```

Expected: `200`.

7. `DELETE /api/v1/documents/{document_id}`
Expected: `204`.

8. `PUT /api/v1/documents/{document_id}/restore`
Expected: `200` for a soft-deleted document.

9. `GET /api/v1/documents/{document_id}/versions`
Expected: `200` with an array of version rows.

10. `GET /api/v1/documents/{document_id}/pages`
Expected: `200` for PDF documents with `document_id`, `page_count`, and `pages`.
Negative check: call it on a non-PDF document and expect `400`.

11. `POST /api/v1/documents/{document_id}/split`

```json
{
  "splits": [
    {
      "start_page": 1,
      "end_page": 2,
      "name": "Purchase Agreement Part 1",
      "doc_type": "purchase_agreement",
      "doc_label": "Pages 1-2"
    },
    {
      "start_page": 3,
      "end_page": 4,
      "name": "Purchase Agreement Part 2",
      "doc_type": "amendment",
      "doc_label": "Pages 3-4"
    }
  ]
}
```

Expected: `200` with new document rows for each successful split.

Useful negative checks:

- Upload an unsupported file type and expect `415`
- Upload a file over 20 MB and expect `413`
- Try `/pages` or `/split` on a non-PDF document and expect `400`

## 23. Communication Logs APIs

Communication logs are append-only. There is no update or delete route.

1. `POST /api/v1/communication-logs`

```json
{
  "channel": "email",
  "direction": "outbound",
  "transaction_id": "<transaction_id>",
  "sender_email": "agent.swagger@example.com",
  "recipient_emails": ["buyer@example.com"],
  "cc_emails": ["coordinator@example.com"],
  "subject": "Inspection scheduled",
  "body": "Inspection is set for Friday at 10 AM.",
  "body_html": null,
  "attachment_ids": [],
  "is_ai_generated": false,
  "ai_confidence": null,
  "ai_assumptions": []
}
```

Expected: `201`.

2. `GET /api/v1/communication-logs`

Useful query params:

- `transaction_id=<transaction_id>`
- `channel=email`
- `direction=outbound`
- `page=1&page_size=20`

Expected: `200` with `items`, `total`, `page`, and `page_size`.

3. `GET /api/v1/communication-logs/{log_id}`
Expected: `200`.

4. `GET /api/v1/communication-logs/transaction/{transaction_id}`
Expected: `200` with all logs for the transaction.

## 24. Audit Logs APIs

These are most useful after you have already created, updated, deleted, assigned, uploaded, or parsed data.

1. `GET /api/v1/audit-logs/`

Useful query params:

- `entity_type=transaction`
- `entity_id=<transaction_id>`
- `action=create`
- `user_id=<user_id>`
- `page=1&page_size=50`

Expected: `200` with `items`, `total`, `page`, and `page_size`.
Role note: tenant-wide list is `Admin` only.

2. `GET /api/v1/audit-logs/{entity_type}/{entity_id}`
Expected: `200` with an array of audit rows.
Role note: this route is allowed for `Admin` and `TeamLead`.

## 25. AI Settings APIs

1. `GET /api/v1/settings/ai-provider`
Expected: `200` with `ai_provider` and `ai_provider_config`.

2. `PUT /api/v1/settings/ai-provider`

```json
{
  "ai_provider": "anthropic"
}
```

Expected: `200`.
Negative check: send any value other than `openai` or `anthropic` and expect `400`.

## 26. AI APIs

These routes now use the provider abstraction and the current tenant AI provider setting. The text parsing and file parsing flows are no longer just basic Swagger stubs.

Before running the richer AI tests, make sure your backend `.env` is populated for the provider you want to use.

1. `POST /api/v1/ai/parse`

```json
{
  "content": "Purchase agreement for 123 Main Street with a purchase price of 500000 and closing on 2026-07-15.",
  "document_type": "purchase_agreement"
}
```

Expected: `200` with `extracted`, `confidence`, and `needs_review`.

2. `POST /api/v1/ai/parse-document/{document_id}`
Expected: `200` after you upload a real document first.

What this route exercises:

- document download from storage
- quality assessment
- two-pass extraction
- document update with `ai_extracted_data`
- review routing
- audit logging

3. `POST /api/v1/ai/recommend-tasks`

```json
{
  "transaction_id": "<transaction_id>",
  "current_tasks": [
    {
      "name": "Send Welcome Email",
      "status": "Completed"
    },
    {
      "name": "Order Title Work",
      "status": "Pending"
    }
  ]
}
```

Expected: `200` with `suggestions`, `confidence`, and `needs_review`.

4. `POST /api/v1/ai/refresh-next-steps`
Expected: `200` with `refreshed`.

Optional query param:

- `transaction_id=<transaction_id>`

Use this route after you have transactions plus tasks so `ai_next_step_text` and `ai_next_step_cta` can be refreshed.

## 27. Minimal Regression Checklist

1. Register or log in an `Admin`, `TeamLead`, `Agent`, and `Elf`.
2. Authorize Swagger with one admin token and keep one lower-privilege token for negative checks.
3. Create or identify a team, then test team member add and remove.
4. Create or identify at least one tenant record if you want to cover tenant CRUD.
5. Create a contact and a vendor, then verify vendor contacts.
6. Create a transaction with rich fields and confirm it appears in list, export, dashboard, and history flows.
7. Create task templates, import at least one template by CSV, then generate tasks for a fresh transaction.
8. Exercise task CRUD, task similarity, task summary, vendor carts, and closing checklist.
9. Create transaction assignments and transaction parties.
10. Upload a document, then test get, download, patch, delete, restore, versions, pages, and split.
11. Create a communication log tied to the transaction, then check transaction history and communication-log filters.
12. Run dashboard `ai-briefing`, `sidebar-kpis`, `deal-state-counts`, `transaction-cards`, and `ai-chat`.
13. Run notifications `pending` and `daily-summary/trigger`.
14. Run `GET /api/v1/settings/ai-provider`, then switch the provider with `PUT /api/v1/settings/ai-provider`.
15. Run `POST /api/v1/ai/parse`, `POST /api/v1/ai/recommend-tasks`, `POST /api/v1/ai/refresh-next-steps`, and `POST /api/v1/ai/parse-document/{document_id}`.
16. Verify audit logs after the CRUD and AI flows above.
17. Confirm at least one `403`, one `404`, one `409`, one `415`, and one `422` from Swagger before signing off.
