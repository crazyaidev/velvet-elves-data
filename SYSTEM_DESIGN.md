# Velvet Elves - System Design Document

**Date:** 2026-03-26
**Scope:** Phase 1 (Milestones 1.1, 1.2, 1.3) aligned to the approved MVP role dashboards and updated requirements
**Reference:** ListedKit.com functionality as design benchmark, adapted for Velvet Elves' approved role-specific dashboard set

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Database Schema Design](#2-database-schema-design)
3. [API Architecture](#3-api-architecture)
4. [Frontend UI/UX Design](#4-frontend-uiux-design)
5. [Phase 1 Implementation Plan](#5-phase-1-implementation-plan)

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENTS                                    │
│   React SPA (Vite + TypeScript)  ·  Future Mobile App             │
└──────────────┬───────────────────────────────────────────────────┘
               │ HTTPS / JWT
┌──────────────▼───────────────────────────────────────────────────┐
│                    AWS EC2 / Docker                                │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              FastAPI Application Server                      │  │
│  │  ┌──────────┐  ┌───────────┐  ┌────────────┐  ┌──────────┐ │  │
│  │  │ Routers  │→ │ Services  │→ │Repositories│→ │ Supabase │ │  │
│  │  │ (API v1) │  │ (Business │  │ (Data      │  │ Client   │ │  │
│  │  │          │  │  Logic)   │  │  Access)   │  │          │ │  │
│  │  └──────────┘  └───────────┘  └────────────┘  └──────────┘ │  │
│  │  ┌──────────┐  ┌───────────┐  ┌────────────┐               │  │
│  │  │   Auth   │  │ AI Engine │  │ Task Engine │               │  │
│  │  │Middleware│  │ (OpenAI)  │  │(Dependency) │               │  │
│  │  └──────────┘  └───────────┘  └────────────┘               │  │
│  └─────────────────────────────────────────────────────────────┘  │
└──────────────┬───────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────┐
│                      SUPABASE                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ PostgreSQL │  │    Auth    │  │  Storage   │  │  Realtime  │  │
│  │   (RLS)    │  │  (GoTrue) │  │  (Buckets) │  │ (Webhooks) │  │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 Layered Architecture

```
Layer           │ Responsibility
────────────────│────────────────────────────────────────────────
Routers         │ HTTP endpoints, request validation, response formatting
Services        │ Business logic, orchestration, authorization
Repositories    │ Data access via Supabase client, PII encryption
Core            │ Auth middleware, config, Supabase client singleton
Models          │ Domain dataclasses (no ORM)
Schemas         │ Pydantic request/response validation
Utils           │ Encryption, security, logging helpers
```

### 1.3 Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | Supabase PostgreSQL | Auth + DB + Storage unified; RLS for multi-tenancy |
| Data Access | supabase-py (PostgREST) | No ORM overhead; aligns with Supabase ecosystem |
| Auth | Supabase Auth (GoTrue) + JWT | OAuth2/JWT; no password storage in app |
| Multi-tenancy | tenant_id + RLS policies | Row-level isolation per brokerage |
| PII | Fernet encryption at rest | email, full_name, phone, address encrypted |
| AI | OpenAI GPT API | Document parsing, email automation, task suggestions |
| File Storage | Supabase Storage | Integrated with auth; signed URLs for access |
| Frontend State | React Query (TanStack) | Server state caching, mutations, optimistic updates |
| UI Components | shadcn/ui + Tailwind | Consistent design system, accessible components |
| FSBO pre-contract work | `property_workspaces` + shared task/doc context | Supports listing-prep and self-guided seller flows before a contract exists |
| Role dashboards | Dedicated dashboard aggregation endpoints by role context | Solo Agent, Team Leader, Attorney, and FSBO all share one shell but need different data contracts |
| Attorney guardrails | Explicit task/document approval gates | AI can prep packets and comparisons, but human legal judgment and release remain human-owned |

### 1.4 Multi-Tenant Architecture

```
Tenant (Brokerage)
  └── Users (Agent, Elf, TeamLead, Attorney, Admin, Client, FSBO, Vendor)
       ├── Property Workspaces
       │    ├── Tasks
       │    ├── Documents
       │    ├── Communication Logs
       │    └── Milestone Share Links
       └── Transactions
            ├── Tasks
            ├── Documents
            ├── Contacts
            ├── Communication Logs
            └── Milestone Share Links
```

- Every data table has `tenant_id` column
- Supabase RLS policies enforce tenant isolation
- Tenant configuration stores branding (logo, colors, domain)
- Admin users manage tenant-level settings

---

## 2. Database Schema Design

### 2.1 Schema Overview (Entity Relationship)

```
tenants ──────────────────────────────────────────┐
  │                                                │
  ├── users ─────┬──── contacts                    │
  │    │         │     (contact_directory)          │
  │    │         ├──── integrations                 │
  │    │         ├──── user_notification_prefs      │
  │    │         └──── invitation_tokens            │
  │    │                                            │
  │    ├── property_workspaces ─┬── workspace_tasks │
  │    │                        ├── workspace_docs  │
  │    │                        ├── workspace_logs  │
  │    │                        └── share_links     │
  │    │                                            │
  │    ├── transactions ──┬── transaction_tasks     │
  │    │    │             ├── transaction_documents  │
  │    │    │             ├── transaction_contacts   │
  │    │    │             ├── transaction_parties    │
  │    │    │             ├── communication_logs     │
  │    │    │             └── share_links            │
  │    │    │                                        │
  │    │    └── transaction_assignments              │
  │    │                                            │
  │    └── task_templates ─── task_template_deps     │
  │                                                │
  └── audit_logs ─────────────────────────────────┘
       confidence_settings
       vendor_lists
```

### 2.2 Complete Table Definitions

#### 2.2.1 `tenants` — Brokerage organizations (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.tenants (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT NOT NULL,
  slug            TEXT NOT NULL UNIQUE,           -- subdomain/url slug
  domain          TEXT,                           -- custom domain (optional)
  logo_url        TEXT,
  primary_color   TEXT DEFAULT '#6366f1',         -- brand color
  secondary_color TEXT DEFAULT '#a78bfa',
  settings_json   JSONB DEFAULT '{}'::jsonb,      -- tenant-level config
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Why:** Multi-tenant isolation requires a first-class tenant entity. Previously `tenant_id` was just a UUID string with no backing table. This table stores brokerage branding for white-label (Milestone 6.1) and acts as the anchor for RLS policies.

#### 2.2.2 `users` — Application profiles (UPDATED)

```sql
CREATE TABLE IF NOT EXISTS public.users (
  id                     UUID PRIMARY KEY,           -- matches auth.users.id
  tenant_id              UUID NOT NULL REFERENCES public.tenants(id),
  email                  TEXT NOT NULL UNIQUE,        -- Fernet encrypted
  full_name              TEXT,                        -- Fernet encrypted
  phone                  TEXT,                        -- Fernet encrypted
  role                   TEXT NOT NULL DEFAULT 'Agent',
  is_active              BOOLEAN NOT NULL DEFAULT TRUE,
  onboarding_completed   BOOLEAN NOT NULL DEFAULT FALSE,
  company_name           TEXT,
  company_logo_url       TEXT,
  bio                    TEXT,                        -- NEW: agent bio for client portal
  avatar_url             TEXT,                        -- NEW: profile photo
  notification_prefs     JSONB DEFAULT '{}'::jsonb,   -- NEW: notification on/off settings
  profile_settings_json  JSONB DEFAULT '{}'::jsonb,   -- NEW: checklist templates, tagged notes,
                                                     --      workspace preferences, first-upload prompts
  team_id                UUID,                        -- NEW: FK to teams (nullable)
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_tenant_id ON public.users (tenant_id);
CREATE INDEX idx_users_role ON public.users (role);
CREATE INDEX idx_users_team_id ON public.users (team_id);
```

**Changes from current:**
- `tenant_id` now references `tenants(id)` (was loose UUID)
- Added `bio`, `avatar_url` for agent profiles / client portal
- Added `notification_prefs` (JSONB) for per-user notification toggles
- Added `profile_settings_json` for printable checklist templates and
  workspace-level preferences
- Added `team_id` for team membership

#### 2.2.3 `teams` — Agent teams within a brokerage (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.teams (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES public.tenants(id),
  name            TEXT NOT NULL,
  lead_user_id    UUID REFERENCES public.users(id),  -- Team Lead
  settings_json   JSONB DEFAULT '{}'::jsonb,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.users
  ADD CONSTRAINT fk_users_team FOREIGN KEY (team_id) REFERENCES public.teams(id);

CREATE INDEX idx_teams_tenant_id ON public.teams (tenant_id);
```

**Why:** Requirements specify Team Lead role with team-wide task template control and team transaction oversight.

#### 2.2.4 `contacts` — Centralized contact directory (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.contacts (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES public.tenants(id),
  created_by      UUID NOT NULL REFERENCES public.users(id),
  contact_type    TEXT NOT NULL,                    -- 'co_agent','loan_officer','title_rep',
                                                   -- 'buyer','seller','inspector','appraiser',
                                                   -- 'home_warranty','other'
  full_name       TEXT NOT NULL,                    -- Fernet encrypted
  email           TEXT,                             -- Fernet encrypted
  phone           TEXT,                             -- Fernet encrypted
  company         TEXT,
  notes           TEXT,
  is_vendor       BOOLEAN DEFAULT FALSE,            -- true if this is a vendor contact
  is_preferred    BOOLEAN DEFAULT FALSE,            -- preferred vendor flag
  state           TEXT,                             -- state where contact operates
  metadata_json   JSONB DEFAULT '{}'::jsonb,        -- extra fields (license#, etc.)
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_contacts_tenant_id ON public.contacts (tenant_id);
CREATE INDEX idx_contacts_created_by ON public.contacts (created_by);
CREATE INDEX idx_contacts_type ON public.contacts (contact_type);
```

**Why:** Requirement 1.3 — centralized contact directory linked to transactions and vendors. Contacts persist across transactions.

#### 2.2.5 `property_workspaces` — FSBO and pre-transaction property-centric work (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.property_workspaces (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL REFERENCES public.tenants(id),
  owner_user_id         UUID NOT NULL REFERENCES public.users(id),
  support_user_id       UUID REFERENCES public.users(id),      -- FSBO guide / internal owner
  linked_transaction_id UUID,                                   -- FK added after transactions table exists

  -- Property info
  address               TEXT NOT NULL,                          -- Fernet encrypted
  city                  TEXT,
  state                 TEXT,
  zip_code              TEXT,
  county                TEXT,

  -- Workspace state
  status                TEXT NOT NULL DEFAULT 'ListingPrep',    -- ListingPrep,UnderContract,Closed,Archived
  lifecycle_stage       TEXT NOT NULL DEFAULT 'prep',           -- prep,listing,under_contract,closing,closed
  target_list_date      DATE,
  target_price          NUMERIC(12,2),
  current_price         NUMERIC(12,2),

  -- Customer-facing helpers
  plain_language_summary TEXT,
  guide_note            TEXT,
  metadata_json         JSONB DEFAULT '{}'::jsonb,

  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_property_workspaces_tenant ON public.property_workspaces (tenant_id);
CREATE INDEX idx_property_workspaces_owner ON public.property_workspaces (owner_user_id);
CREATE INDEX idx_property_workspaces_support ON public.property_workspaces (support_user_id);
CREATE INDEX idx_property_workspaces_status ON public.property_workspaces (status);
```

**Why:** Updated requirements add an FSBO customer workspace that can exist
before a formal transaction is created. This table models listing-prep and
property-centric progress without overloading the transaction lifecycle. Once a
contract is in place, the workspace can link forward to a transaction.

#### 2.2.6 `transactions` — Real estate deals (UPDATED)

```sql
CREATE TABLE IF NOT EXISTS public.transactions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL REFERENCES public.tenants(id),
  property_workspace_id UUID REFERENCES public.property_workspaces(id) ON DELETE SET NULL,
  created_by            UUID NOT NULL REFERENCES public.users(id),  -- renamed from user_id

  -- Property info
  address               TEXT NOT NULL,                 -- Fernet encrypted
  city                  TEXT,
  state                 TEXT,
  zip_code              TEXT,
  county                TEXT,

  -- Transaction details
  use_case              TEXT NOT NULL,                  -- see TransactionUseCase enum
  financing_type        TEXT NOT NULL DEFAULT 'Financed', -- 'Cash' | 'Financed'
  representation_type   TEXT NOT NULL DEFAULT 'Buyer',    -- 'Buyer' | 'Seller' | 'Both'
  closing_mode          TEXT NOT NULL DEFAULT 'TitleEscrow', -- 'AttorneyClosing' | 'TitleEscrow' | 'SharedApproval'
  purchase_price        NUMERIC(12,2),
  earnest_money         NUMERIC(12,2),

  -- Key dates
  contract_acceptance_date DATE,
  closing_date             DATE,
  possession_date          DATE,
  inspection_response_sent_at TIMESTAMPTZ,

  -- Inspection
  has_inspection          BOOLEAN DEFAULT TRUE,
  inspection_days         INTEGER,
  inspection_response_days INTEGER,

  -- HOA
  has_hoa                 BOOLEAN DEFAULT FALSE,
  hoa_doc_days            INTEGER,

  -- Home Warranty
  has_home_warranty       BOOLEAN DEFAULT FALSE,
  warranty_ordered_by     TEXT,                         -- 'us' | 'other_party'

  -- Title
  title_ordered_by        TEXT,                         -- 'us' | 'other_party'

  -- Insurance
  insurance_commitment_days INTEGER,

  -- Financing specific
  is_owner_occupied       BOOLEAN DEFAULT TRUE,

  -- Status
  status                  TEXT NOT NULL DEFAULT 'Active',
  notes                   TEXT,
  wizard_completed        BOOLEAN DEFAULT FALSE,

  -- Metadata
  attorney_rule_context   JSONB DEFAULT '{}'::jsonb,    -- state-closing profile / release timing flags
  metadata_json           JSONB DEFAULT '{}'::jsonb,    -- extensible fields
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_transactions_tenant_id ON public.transactions (tenant_id);
CREATE INDEX idx_transactions_property_workspace ON public.transactions (property_workspace_id);
CREATE INDEX idx_transactions_created_by ON public.transactions (created_by);
CREATE INDEX idx_transactions_status ON public.transactions (status);
CREATE INDEX idx_transactions_closing_date ON public.transactions (closing_date);
CREATE INDEX idx_transactions_use_case ON public.transactions (use_case);
CREATE INDEX idx_transactions_closing_mode ON public.transactions (closing_mode);

ALTER TABLE public.property_workspaces
  ADD CONSTRAINT fk_property_workspace_transaction
  FOREIGN KEY (linked_transaction_id) REFERENCES public.transactions(id);
```

**Major changes from current:**
- Expanded from 4 fields to full transaction model matching requirements
- `use_case` now maps to 6 types: `Buy-Fin`, `Buy-Cash`, `Sell-Fin`, `Sell-Cash`, `Both-Fin`, `Both-Cash`
- Added all wizard-derived fields: inspection, HOA, home warranty, title, insurance, financing
- Added `representation_type` and `financing_type` as separate fields
- Added `closing_mode` to support attorney-closing vs title/escrow vs shared approval workflows
- Added `property_workspace_id` to convert FSBO/prep work into a formal transaction without losing context
- Added `inspection_response_sent_at` to support the "In Inspection" dashboard state directly
- Added `attorney_rule_context` for state-based closing and release/disbursement logic
- `user_id` renamed to `created_by` for clarity
- Property address split into components (city, state, zip, county)
- `metadata_json` for extensibility without schema changes

#### 2.2.7 `transaction_assignments` — Who works on a transaction (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.transaction_assignments (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id  UUID NOT NULL REFERENCES public.transactions(id) ON DELETE CASCADE,
  user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  role_in_transaction TEXT NOT NULL,               -- 'primary_agent','elf','team_lead','attorney'
  assigned_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  assigned_by     UUID REFERENCES public.users(id),
  is_active       BOOLEAN DEFAULT TRUE,
  UNIQUE (transaction_id, user_id, role_in_transaction)
);

CREATE INDEX idx_tx_assign_transaction ON public.transaction_assignments (transaction_id);
CREATE INDEX idx_tx_assign_user ON public.transaction_assignments (user_id);
```

**Why:** Requirement 2.3 now explicitly includes attorney assignment in
addition to agent/elf/team participation.

#### 2.2.8 `transaction_parties` — External parties on a deal (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.transaction_parties (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id  UUID NOT NULL REFERENCES public.transactions(id) ON DELETE CASCADE,
  contact_id      UUID REFERENCES public.contacts(id),       -- link to contacts directory
  party_role      TEXT NOT NULL,                               -- 'buyer','seller','listing_agent',
                                                               -- 'buyers_agent','loan_officer',
                                                               -- 'title_rep','title_company',
                                                               -- 'closing_attorney','settlement_attorney',
                                                               -- 'inspector','appraiser',
                                                               -- 'home_warranty_company','other'
  full_name       TEXT,                                        -- Fernet encrypted (denormalized)
  email           TEXT,                                        -- Fernet encrypted
  phone           TEXT,                                        -- Fernet encrypted
  company         TEXT,
  is_primary      BOOLEAN DEFAULT TRUE,
  source          TEXT DEFAULT 'manual',                        -- 'manual','ai_extracted','imported'
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tx_parties_transaction ON public.transaction_parties (transaction_id);
CREATE INDEX idx_tx_parties_contact ON public.transaction_parties (contact_id);
CREATE INDEX idx_tx_parties_role ON public.transaction_parties (party_role);
```

**Why:** Wizard extracts party data from documents. Parties are linked back to the contact directory for reuse. This maps to the "vendor contact card" feature and connected contacts.

#### 2.2.9 `task_templates` — Master task library (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.task_templates (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id           UUID REFERENCES public.tenants(id),       -- NULL = system-wide default
  team_id             UUID REFERENCES public.teams(id),         -- NULL = not team-specific
  created_by          UUID REFERENCES public.users(id),

  -- From REWORKING_TASK_DB.csv
  legacy_task_id      INTEGER,                                   -- original Task ID from CSV
  name                TEXT NOT NULL,
  description         TEXT,
  target              TEXT,                                      -- who: 'Agent','Buyer','Seller',
                                                                 -- 'Co-op Agent','Loan Officer',
                                                                 -- 'Title','Attorney','FSBO',etc.
  cc_targets          TEXT[],                                     -- CC recipients
  milestone_label     TEXT,                                       -- 'Offer Accepted','Title Work Ordered',
                                                                 -- 'Inspection Scheduled', etc.
  -- Use case applicability (which of the 6 transaction types)
  use_cases           TEXT[] NOT NULL DEFAULT '{}',               -- e.g. {'Buy-Fin','Buy-Cash'}
  context_scope       TEXT NOT NULL DEFAULT 'transaction',        -- 'transaction','property_workspace','shared'

  -- Dependency configuration
  dep_rel             TEXT DEFAULT 'FS',                          -- 'FS' (Finish-Start) or 'SS' (Start-Start)
  dep_task_id         INTEGER,                                   -- legacy task ID this depends on
  float_days          TEXT,                                       -- can be integer or formula ref
                                                                 -- e.g. '0', '14', 'wizard:hoa_doc_days'

  -- Automation
  automation_level    TEXT NOT NULL DEFAULT 'Manual',             -- 'Automated','ToBeAutomated','Manual'
  requires_human_approval BOOLEAN NOT NULL DEFAULT FALSE,
  approval_role       TEXT,                                       -- e.g. 'Attorney','TeamLead'
  customer_visible_default BOOLEAN NOT NULL DEFAULT FALSE,

  -- Conditional logic
  conditions_json     JSONB DEFAULT '[]'::jsonb,                  -- wizard field conditions
                                                                 -- e.g. [{"field":"has_inspection","value":true}]
  both_rep_behavior   TEXT,                                       -- 'single_instance','skip','replace_with'
  replace_with_id     INTEGER,                                   -- if both_rep_behavior='replace_with'

  -- Category for UI grouping
  category            TEXT,                                       -- 'welcome','documentation','vendor',
                                                                 -- 'closing','follow_up','meta'
  sort_order          INTEGER DEFAULT 0,

  is_active           BOOLEAN DEFAULT TRUE,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_task_templates_tenant ON public.task_templates (tenant_id);
CREATE INDEX idx_task_templates_team ON public.task_templates (team_id);
CREATE INDEX idx_task_templates_legacy ON public.task_templates (legacy_task_id);
CREATE INDEX idx_task_templates_scope ON public.task_templates (context_scope);
```

**Why:** This is the master task catalog for both formal transactions and
property-centric prep work. Key design decisions:
- `legacy_task_id` preserves original numbering for dependency references
- `context_scope` lets one template library serve transaction workflows,
  FSBO/property prep flows, and shared reusable tasks
- `requires_human_approval` and `approval_role` allow attorney or team-lead
  review gates without duplicating task templates
- `customer_visible_default` supports customer-facing progress states in FSBO
  and client experiences
- Supports system-wide (`tenant_id = NULL`), per-tenant, and per-team templates

#### 2.2.10 `tasks` — Transaction- and property-specific task instances (UPDATED)

```sql
CREATE TABLE IF NOT EXISTS public.tasks (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id    UUID REFERENCES public.transactions(id) ON DELETE CASCADE,
  property_workspace_id UUID REFERENCES public.property_workspaces(id) ON DELETE CASCADE,
  template_id       UUID REFERENCES public.task_templates(id),    -- which template spawned this

  -- Task details (copied from template, can be overridden)
  name              TEXT NOT NULL,
  description       TEXT,
  target            TEXT,                             -- who is responsible
  cc_targets        TEXT[],
  milestone_label   TEXT,
  completion_method TEXT,                             -- 'phone_call','email',
                                                     -- 'e_signature','in_person',
                                                     -- 'upload_document','online_portal',
                                                     -- 'ai_agent','other'

  -- Scheduling
  due_date          DATE,
  completed_at      TIMESTAMPTZ,
  float_days        REAL,
  dep_rel           TEXT DEFAULT 'FS',

  -- Status
  status            TEXT NOT NULL DEFAULT 'Pending',   -- Pending,InProgress,Completed,Blocked,Skipped
  automation_level  TEXT NOT NULL DEFAULT 'Manual',

  -- Dependencies (resolved to actual task UUIDs for this transaction)
  dependencies_json JSONB DEFAULT '[]'::jsonb,

  -- Visibility and customer-facing copy
  customer_visible  BOOLEAN NOT NULL DEFAULT FALSE,
  customer_summary  TEXT,

  -- Approval workflow
  requires_human_approval BOOLEAN NOT NULL DEFAULT FALSE,
  approval_role     TEXT,                              -- e.g. 'Attorney','TeamLead'
  approval_status   TEXT NOT NULL DEFAULT 'not_required', -- 'not_required','pending_review','approved','changes_requested','rejected'
  approved_by       UUID REFERENCES public.users(id),
  approved_at       TIMESTAMPTZ,

  -- AI recommendation tracking
  source            TEXT DEFAULT 'template',           -- 'template','ai_recommended','manual'
  ai_reason         TEXT,                              -- why AI recommended this task
  ai_confidence     REAL,                              -- confidence score 0-1

  -- Ordering and metadata
  sort_order        INTEGER NOT NULL DEFAULT 0,
  notes             TEXT,
  metadata_json     JSONB DEFAULT '{}'::jsonb,

  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT chk_tasks_context
    CHECK (transaction_id IS NOT NULL OR property_workspace_id IS NOT NULL)
);

CREATE INDEX idx_tasks_transaction_id ON public.tasks (transaction_id);
CREATE INDEX idx_tasks_property_workspace ON public.tasks (property_workspace_id);
CREATE INDEX idx_tasks_template_id ON public.tasks (template_id);
CREATE INDEX idx_tasks_status ON public.tasks (status);
CREATE INDEX idx_tasks_due_date ON public.tasks (due_date);
CREATE INDEX idx_tasks_target ON public.tasks (target);
CREATE INDEX idx_tasks_approval_status ON public.tasks (approval_status);
```

**Major changes from current:**
- Added `property_workspace_id` so FSBO/listing-prep tasks exist before a
  formal transaction is opened
- Added `customer_visible` and `customer_summary` for customer-friendly
  milestone explanations
- Added `requires_human_approval`, `approval_role`, and `approval_status` to
  support attorney and oversight queues
- `transaction_id` is no longer mandatory as long as a property workspace exists
- Added `template_id` linking back to source template
- Added `target`, `cc_targets`, `milestone_label` from task DB
- Added `completion_method` so manual tasks align with the new Add Task flow
- `due_date` is now proper DATE (was TEXT)
- Added `completed_at` timestamp
- `dependencies_json` is now JSONB (was TEXT)
- Added AI recommendation fields (`source`, `ai_reason`, `ai_confidence`)
- Added `notes` for task-specific annotations

#### 2.2.11 `documents` — Uploaded files and legal packets (UPDATED)

```sql
CREATE TABLE IF NOT EXISTS public.documents (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES public.tenants(id),
  transaction_id    UUID REFERENCES public.transactions(id) ON DELETE SET NULL,
  property_workspace_id UUID REFERENCES public.property_workspaces(id) ON DELETE SET NULL,
  uploaded_by       UUID NOT NULL REFERENCES public.users(id),

  -- File info
  file_name         TEXT NOT NULL,
  original_name     TEXT NOT NULL,                    -- original upload name
  storage_path      TEXT NOT NULL,                    -- Supabase Storage path
  mime_type         TEXT,
  size_bytes        BIGINT,

  -- Document classification
  doc_type          TEXT,                              -- 'purchase_agreement','counter_offer',
                                                      -- 'amendment','pre_approval','title_work',
                                                      -- 'title_commitment','settlement_statement',
                                                      -- 'affidavit','recording_packet',
                                                      -- 'inspection_report','hoa_docs',
                                                      -- 'closing_disclosure','utility_info',
                                                      -- 'sellers_disclosure','blc_tax_sheet',
                                                      -- 'earnest_money','listing_photos',
                                                      -- 'property_condition_packet','other'
  doc_label         TEXT,                              -- user-friendly display label

  -- Version control
  version           INTEGER NOT NULL DEFAULT 1,
  parent_id         UUID REFERENCES public.documents(id),  -- previous version
  is_current        BOOLEAN DEFAULT TRUE,
  is_legacy         BOOLEAN DEFAULT FALSE,            -- marked as outdated by vendor re-upload

  -- Status
  status            TEXT NOT NULL DEFAULT 'pending',   -- pending,processed,failed,archived
  review_status     TEXT NOT NULL DEFAULT 'not_required', -- 'not_required','pending_review','approved','changes_requested','rejected'
  review_required_role TEXT,                           -- e.g. 'Attorney'
  reviewed_by       UUID REFERENCES public.users(id),
  reviewed_at       TIMESTAMPTZ,
  is_formal_legal_doc BOOLEAN NOT NULL DEFAULT FALSE,
  portal_visibility TEXT NOT NULL DEFAULT 'internal',  -- 'internal','client_portal','fsbo_portal','timeline_share'
  is_deleted        BOOLEAN DEFAULT FALSE,             -- soft delete
  deleted_at        TIMESTAMPTZ,
  deleted_by        UUID REFERENCES public.users(id),
  deletion_reason   TEXT,

  -- AI processing
  ai_extracted_data JSONB,                             -- parsed fields from AI
  ai_confidence     REAL,

  -- Signature tracking
  is_signed         BOOLEAN,
  signature_status  TEXT,                              -- 'pending','sent_for_signature','signed','not_required'
  esign_envelope_id TEXT,                              -- DocuSign/HelloSign envelope ID

  metadata_json     JSONB DEFAULT '{}'::jsonb,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_documents_tenant ON public.documents (tenant_id);
CREATE INDEX idx_documents_transaction ON public.documents (transaction_id);
CREATE INDEX idx_documents_property_workspace ON public.documents (property_workspace_id);
CREATE INDEX idx_documents_uploaded_by ON public.documents (uploaded_by);
CREATE INDEX idx_documents_type ON public.documents (doc_type);
CREATE INDEX idx_documents_parent ON public.documents (parent_id);
CREATE INDEX idx_documents_review_status ON public.documents (review_status);
```

**Changes from current:**
- Added `property_workspace_id` so property prep files and FSBO artifacts can
  exist before transaction conversion
- Added legal review workflow fields (`review_status`, `review_required_role`,
  `reviewed_by`, `reviewed_at`)
- Added `is_formal_legal_doc` and `portal_visibility` for attorney guardrails
  and customer-safe document presentation
- Expanded `doc_type` to cover attorney closing packets and FSBO listing-prep docs
- Added version control (`version`, `parent_id`, `is_current`, `is_legacy`)
- Added document classification (`doc_type`, `doc_label`)
- Added soft delete fields
- Added AI extraction storage (`ai_extracted_data`, `ai_confidence`)
- Added signature tracking fields
- Renamed `user_id` to `uploaded_by`

#### 2.2.12 `communication_logs` — Immutable communication record (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.communication_logs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES public.tenants(id),
  transaction_id    UUID REFERENCES public.transactions(id) ON DELETE SET NULL,
  property_workspace_id UUID REFERENCES public.property_workspaces(id) ON DELETE SET NULL,

  -- Who
  sender_user_id    UUID REFERENCES public.users(id),
  sender_email      TEXT,                              -- for external senders
  recipient_emails  TEXT[],
  cc_emails         TEXT[],

  -- What
  channel           TEXT NOT NULL,                     -- 'email','sms','voice_call','push',
                                                      -- 'system','ai_draft','note','document_action'
  direction         TEXT NOT NULL,                     -- 'inbound','outbound','internal'
  subject           TEXT,
  body              TEXT,
  body_html         TEXT,
  visibility_scope  TEXT NOT NULL DEFAULT 'internal', -- 'internal','client_portal','fsbo_portal','timeline_share'

  -- Attachments
  attachment_ids    UUID[],                            -- references to documents

  -- AI tracking
  is_ai_generated   BOOLEAN DEFAULT FALSE,
  ai_confidence     REAL,
  ai_assumptions    TEXT[],                            -- bolded items in AI drafts
  approval_status   TEXT,                              -- 'auto_sent','pending_review','approved','rejected'
  approved_by       UUID REFERENCES public.users(id),
  approved_at       TIMESTAMPTZ,

  -- Provider / external reference tracking
  provider_name     TEXT,                              -- e.g. gmail, outlook, twilio
  provider_ref_id   TEXT,                              -- message SID / call SID / external id

  -- Status
  status            TEXT DEFAULT 'sent',               -- 'draft','sent','failed','pending_review'
  error_message     TEXT,

  -- Immutability note: rows should never be updated, only appended
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_comm_logs_tenant ON public.communication_logs (tenant_id);
CREATE INDEX idx_comm_logs_transaction ON public.communication_logs (transaction_id);
CREATE INDEX idx_comm_logs_property_workspace ON public.communication_logs (property_workspace_id);
CREATE INDEX idx_comm_logs_sender ON public.communication_logs (sender_user_id);
CREATE INDEX idx_comm_logs_channel ON public.communication_logs (channel);
CREATE INDEX idx_comm_logs_created ON public.communication_logs (created_at);
```

**Why:** Requirement 6.1 calls for one immutable communication log across
transactions, property workspaces, AI drafts, and customer-safe timeline events.
No `updated_at` exists because rows are append-only.

#### 2.2.13 `milestone_share_links` — Read-only milestone sharing (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.milestone_share_links (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES public.tenants(id),
  transaction_id    UUID REFERENCES public.transactions(id) ON DELETE CASCADE,
  property_workspace_id UUID REFERENCES public.property_workspaces(id) ON DELETE CASCADE,
  created_by        UUID NOT NULL REFERENCES public.users(id),

  recipient_email   TEXT,                              -- optional prefilled recipient
  token             TEXT NOT NULL UNIQUE,
  scope             TEXT NOT NULL DEFAULT 'milestones_read_only',
  expires_at        TIMESTAMPTZ,
  notify_on_view    BOOLEAN NOT NULL DEFAULT TRUE,
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  view_count        INTEGER NOT NULL DEFAULT 0,
  last_viewed_at    TIMESTAMPTZ,
  metadata_json     JSONB DEFAULT '{}'::jsonb,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT chk_share_link_context
    CHECK (transaction_id IS NOT NULL OR property_workspace_id IS NOT NULL)
);

CREATE INDEX idx_share_links_tenant ON public.milestone_share_links (tenant_id);
CREATE INDEX idx_share_links_transaction ON public.milestone_share_links (transaction_id);
CREATE INDEX idx_share_links_property_workspace ON public.milestone_share_links (property_workspace_id);
CREATE INDEX idx_share_links_token ON public.milestone_share_links (token);
```

**Why:** Requirement 1.7 calls for expirable, read-only milestone sharing for
clients and FSBO customers without granting full app access.

#### 2.2.14 `audit_logs` — System-wide audit trail (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.audit_logs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES public.tenants(id),
  user_id         UUID REFERENCES public.users(id),
  user_role       TEXT,

  -- What happened
  action          TEXT NOT NULL,                       -- 'create','update','delete','login',
                                                      -- 'assign','complete','approve','reject',
                                                      -- 'ai_extract','ai_recommend','ai_send'
  entity_type     TEXT NOT NULL,                       -- 'transaction','property_workspace',
                                                      -- 'task','document','share_link',
                                                      -- 'user','contact','communication','template'
  entity_id       UUID,

  -- Change details
  before_state    JSONB,                               -- snapshot before change
  after_state     JSONB,                               -- snapshot after change
  summary         TEXT,                                -- human-readable: "Task X due date changed from Y to Z"

  -- Context
  ip_address      TEXT,
  user_agent      TEXT,
  request_id      TEXT,                                -- correlation ID

  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_tenant ON public.audit_logs (tenant_id);
CREATE INDEX idx_audit_user ON public.audit_logs (user_id);
CREATE INDEX idx_audit_entity ON public.audit_logs (entity_type, entity_id);
CREATE INDEX idx_audit_action ON public.audit_logs (action);
CREATE INDEX idx_audit_created ON public.audit_logs (created_at);
```

**Why:** Requirement 10.3 requires all approvals, overrides, share-link access,
and customer-visible changes to remain fully auditable.

#### 2.2.15 `invitation_tokens` — Invite-based onboarding (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.invitation_tokens (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES public.tenants(id),
  invited_by      UUID NOT NULL REFERENCES public.users(id),
  email           TEXT NOT NULL,                       -- Fernet encrypted
  role            TEXT NOT NULL DEFAULT 'Agent',
  team_id         UUID REFERENCES public.teams(id),
  transaction_id  UUID REFERENCES public.transactions(id),  -- if invited to a specific transaction
  property_workspace_id UUID REFERENCES public.property_workspaces(id),
  token           TEXT NOT NULL UNIQUE,
  expires_at      TIMESTAMPTZ NOT NULL,
  used_at         TIMESTAMPTZ,
  is_used         BOOLEAN DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_invitations_token ON public.invitation_tokens (token);
CREATE INDEX idx_invitations_tenant ON public.invitation_tokens (tenant_id);
```

**Why:** Requirement 1.1 still uses invitation onboarding, but now the invite
may target a team, a transaction, or a property workspace for Attorney and
FSBO-specific access.

#### 2.2.16 `confidence_settings` — AI confidence thresholds (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.confidence_settings (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID REFERENCES public.tenants(id),
  team_id               UUID REFERENCES public.teams(id),

  -- Global settings (admin-controlled)
  global_min_floor      REAL DEFAULT 0.75,             -- minimum confidence for any auto-action
  auto_proceed_threshold REAL DEFAULT 0.90,            -- "ship it" tier
  review_threshold      REAL DEFAULT 0.75,             -- "I better see it first" tier
  legal_review_threshold REAL DEFAULT 0.85,            -- never auto-complete attorney-sensitive work
  customer_visible_threshold REAL DEFAULT 0.85,        -- customer-facing language/docs need higher confidence

  -- Task-specific overrides
  task_overrides_json   JSONB DEFAULT '{}'::jsonb,     -- {"task_category": {"threshold": 0.85}}

  created_by            UUID REFERENCES public.users(id),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (tenant_id, team_id)
);
```

**Why:** Requirement 4.7 now needs separate thresholds for general automation,
attorney-reviewed outputs, and customer-visible content.

#### 2.2.17 `integrations` — Email/OAuth connections (EXISTING, minimal updates)

Already in the schema. Phase 1 continues to use the current integrations model,
with dashboard and communication services consuming provider metadata for email,
calendar, and notifications.

### 2.3 Updated Enums

```python
class UserRole(str, enum.Enum):
    AGENT = "Agent"
    ELF = "Elf"
    TEAM_LEAD = "TeamLead"
    ATTORNEY = "Attorney"
    ADMIN = "Admin"
    CLIENT = "Client"
    FSBO = "FSBO"
    VENDOR = "Vendor"

class TransactionUseCase(str, enum.Enum):
    BUY_FIN = "Buy-Fin"        # Buyer - Financing
    BUY_CASH = "Buy-Cash"      # Buyer - Cash
    SELL_FIN = "Sell-Fin"       # Seller - Financing
    SELL_CASH = "Sell-Cash"     # Seller - Cash
    BOTH_FIN = "Both-Fin"      # Buyer & Seller - Financing
    BOTH_CASH = "Both-Cash"    # Buyer & Seller - Cash

class TransactionStatus(str, enum.Enum):
    ACTIVE = "Active"
    INCOMPLETE = "Incomplete"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    CLOSED = "Closed"

class PropertyWorkspaceStatus(str, enum.Enum):
    LISTING_PREP = "ListingPrep"
    LIVE_MARKETING = "LiveMarketing"
    UNDER_CONTRACT = "UnderContract"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"

class ClosingMode(str, enum.Enum):
    TITLE_ESCROW = "TitleEscrow"
    ATTORNEY = "Attorney"
    HYBRID = "Hybrid"

class TaskStatus(str, enum.Enum):
    PENDING = "Pending"
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"
    BLOCKED = "Blocked"
    SKIPPED = "Skipped"

class ApprovalStatus(str, enum.Enum):
    NOT_REQUIRED = "not_required"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"

class AutomationLevel(str, enum.Enum):
    AUTOMATED = "Automated"
    TO_BE_AUTOMATED = "ToBeAutomated"
    AI_ASSISTED = "AIAssisted"
    MANUAL = "Manual"

class DepRelType(str, enum.Enum):
    FS = "FS"    # Finish-Start: task starts after dependency finishes
    SS = "SS"    # Start-Start: task starts relative to dependency start

class DocumentType(str, enum.Enum):
    PURCHASE_AGREEMENT = "purchase_agreement"
    COUNTER_OFFER = "counter_offer"
    AMENDMENT = "amendment"
    PRE_APPROVAL = "pre_approval"
    TITLE_WORK = "title_work"
    TITLE_COMMITMENT = "title_commitment"
    SETTLEMENT_STATEMENT = "settlement_statement"
    AFFIDAVIT = "affidavit"
    RECORDING_PACKET = "recording_packet"
    INSPECTION_REPORT = "inspection_report"
    HOA_DOCS = "hoa_docs"
    CLOSING_DISCLOSURE = "closing_disclosure"
    UTILITY_INFO = "utility_info"
    SELLERS_DISCLOSURE = "sellers_disclosure"
    BLC_TAX_SHEET = "blc_tax_sheet"
    EARNEST_MONEY = "earnest_money"
    LISTING_PHOTOS = "listing_photos"
    PROPERTY_CONDITION_PACKET = "property_condition_packet"
    HOME_WARRANTY = "home_warranty"
    INSURANCE = "insurance"
    OTHER = "other"

class ContactType(str, enum.Enum):
    CO_AGENT = "co_agent"
    LOAN_OFFICER = "loan_officer"
    TITLE_REP = "title_rep"
    ATTORNEY = "attorney"
    SUPPORT_GUIDE = "support_guide"
    BUYER = "buyer"
    SELLER = "seller"
    INSPECTOR = "inspector"
    APPRAISER = "appraiser"
    HOME_WARRANTY = "home_warranty"
    OTHER = "other"

class CommunicationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    VOICE_CALL = "voice_call"
    PUSH = "push"
    SYSTEM = "system"
    AI_DRAFT = "ai_draft"
    NOTE = "note"
    DOCUMENT_ACTION = "document_action"
```

### 2.4 Row Level Security (RLS) Policies

```sql
-- Enable RLS on all tables
ALTER TABLE public.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.property_workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.communication_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.milestone_share_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Policy: users can only see data within their tenant
CREATE POLICY tenant_isolation_users ON public.users
  USING (tenant_id = (
    SELECT tenant_id FROM public.users WHERE id = auth.uid()
  ));

CREATE POLICY tenant_isolation_transactions ON public.transactions
  USING (tenant_id = (
    SELECT tenant_id FROM public.users WHERE id = auth.uid()
  ));

CREATE POLICY tenant_isolation_property_workspaces ON public.property_workspaces
  USING (tenant_id = (
    SELECT tenant_id FROM public.users WHERE id = auth.uid()
  ));

CREATE POLICY tenant_isolation_share_links ON public.milestone_share_links
  USING (tenant_id = (
    SELECT tenant_id FROM public.users WHERE id = auth.uid()
  ));

-- Similar policies for all other tables...
-- Public share-link reads should use a separate security-definer function that
-- validates token, expiry, and visibility scope without exposing tenant data.
-- Note: Service role key bypasses RLS for backend operations
```

### 2.5 Task Template Import Strategy (from REWORKING_TASK_DB.csv)

The CSV contains 50+ tasks with this mapping:

| CSV Column | DB Column | Notes |
|------------|-----------|-------|
| Task Name | name | Direct mapping |
| Task ID | legacy_task_id | Preserved for dependency references |
| Use Case | use_cases | Parse comma-separated into TEXT[] |
| Target | target | Direct mapping |
| CC: | cc_targets | Parse into TEXT[] |
| Milestone Task | milestone_label | Direct mapping |
| Deprel | dep_rel | 'FS' or 'SS' |
| Task Dependent | dep_task_id | References legacy_task_id |
| Float | float_days | Number or wizard field reference |
| Development Notes | conditions_json | Parse into conditional logic |
| Additional Notes | metadata_json | Store as metadata |
| Task Description | description | Direct mapping |
| MStone | milestone_label | Secondary milestone reference |

Special handling:
- **"Both" representation rules**: Parse "Development Notes" and "Additional Notes" for `both_rep_behavior`:
  - "If Both is selected, this task instance does not populate" → `both_rep_behavior = 'skip'`
  - "If Both is selected, only one task instance is created" → `both_rep_behavior = 'single_instance'`
  - "This task is to populate, instead of task X & Y when Both" → `both_rep_behavior = 'replace_with'`
- **Wizard-dependent floats**: "# of Days for HOA Doc Delivery Period entered in the wizard" → `float_days = 'wizard:hoa_doc_days'`
- **Wizard-dependent conditions**: "If answer is no, this task does not populate" → `conditions_json = [{"field": "has_inspection", "value": true}]`

---

## 3. API Architecture

### 3.1 API Design Principles

- RESTful with consistent naming: `/api/v1/{resource}`
- JWT Bearer auth on all protected endpoints
- Pydantic request/response validation
- Tenant isolation enforced at service layer
- Pagination via `?page=1&page_size=20`
- Filtering via query params: `?status=Active&use_case=Buy-Fin`
- Sorting via `?sort_by=closing_date&sort_order=asc`
- All mutations return the updated resource
- Webhook hooks for external integrations

### 3.2 Phase 1 API Endpoints

#### Auth & Users (`/api/v1/auth`, `/api/v1/users`)

```
POST   /api/v1/auth/register              # Register new user
POST   /api/v1/auth/login                 # Login (Supabase Auth)
POST   /api/v1/auth/logout                # Logout
POST   /api/v1/auth/password-reset        # Request password reset
POST   /api/v1/auth/password-reset/confirm # Confirm password reset
POST   /api/v1/auth/refresh               # Refresh JWT token
GET    /api/v1/auth/me                    # Get current user profile

GET    /api/v1/users                      # List users (Admin/TeamLead)
GET    /api/v1/users/{id}                 # Get user by ID
PUT    /api/v1/users/{id}                 # Update user profile
PUT    /api/v1/users/{id}/role            # Change user role (Admin only)
DELETE /api/v1/users/{id}                 # Deactivate user (Admin only)

POST   /api/v1/users/invite              # Send invitation (Agent/TeamLead/Admin)
GET    /api/v1/users/invite/{token}       # Validate invitation token
POST   /api/v1/users/invite/{token}/accept # Accept invitation & register
```

#### Teams (`/api/v1/teams`)

```
POST   /api/v1/teams                      # Create team (Admin)
GET    /api/v1/teams                      # List teams
GET    /api/v1/teams/{id}                 # Get team details
PUT    /api/v1/teams/{id}                 # Update team
DELETE /api/v1/teams/{id}                 # Delete team
POST   /api/v1/teams/{id}/members         # Add member to team
DELETE /api/v1/teams/{id}/members/{userId} # Remove member from team
```

#### Contacts (`/api/v1/contacts`)

```
POST   /api/v1/contacts                   # Create contact
GET    /api/v1/contacts                   # List contacts (with filters)
GET    /api/v1/contacts/{id}              # Get contact
PUT    /api/v1/contacts/{id}              # Update contact
DELETE /api/v1/contacts/{id}              # Soft delete contact
GET    /api/v1/contacts/search            # Search contacts by name/email/company
```

#### Property Workspaces (`/api/v1/property-workspaces`)

```
POST   /api/v1/property-workspaces                 # Create FSBO/listing-prep workspace
GET    /api/v1/property-workspaces                 # List workspaces (filtered by role/status)
GET    /api/v1/property-workspaces/{id}            # Get workspace detail
PUT    /api/v1/property-workspaces/{id}            # Update property/workspace data
DELETE /api/v1/property-workspaces/{id}            # Archive workspace

POST   /api/v1/property-workspaces/{id}/convert-to-transaction # Promote to formal deal
GET    /api/v1/property-workspaces/{id}/tasks      # List workspace tasks
GET    /api/v1/property-workspaces/{id}/documents  # List workspace documents
GET    /api/v1/property-workspaces/{id}/activity   # Timeline/activity feed
```

#### Transactions (`/api/v1/transactions`)

```
POST   /api/v1/transactions               # Create transaction
GET    /api/v1/transactions               # List transactions (filtered by role)
GET    /api/v1/transactions/{id}          # Get transaction detail
PUT    /api/v1/transactions/{id}          # Update transaction
DELETE /api/v1/transactions/{id}          # Soft delete transaction
PUT    /api/v1/transactions/{id}/status   # Change status
PUT    /api/v1/transactions/{id}/use-case # Change use case (targeted task update)
PUT    /api/v1/transactions/{id}/closing-mode # Set title/attorney/hybrid closing path

POST   /api/v1/transactions/{id}/assignments          # Assign user to transaction
GET    /api/v1/transactions/{id}/assignments          # List assignments
DELETE /api/v1/transactions/{id}/assignments/{assignId} # Remove assignment

POST   /api/v1/transactions/{id}/parties              # Add party to transaction
GET    /api/v1/transactions/{id}/parties              # List parties
PUT    /api/v1/transactions/{id}/parties/{partyId}    # Update party
DELETE /api/v1/transactions/{id}/parties/{partyId}    # Remove party
```

#### Task Templates (`/api/v1/task-templates`)

```
POST   /api/v1/task-templates             # Create template (Admin/TeamLead)
GET    /api/v1/task-templates             # List templates (with filters)
GET    /api/v1/task-templates/{id}        # Get template
PUT    /api/v1/task-templates/{id}        # Update template
DELETE /api/v1/task-templates/{id}        # Deactivate template

POST   /api/v1/task-templates/import      # Import from CSV (Admin)
GET    /api/v1/task-templates/by-use-case/{useCase} # Get templates for a use case
GET    /api/v1/task-templates/by-context/{scope}    # transaction/property_workspace/shared
```

#### Tasks (`/api/v1/tasks`)

```
POST   /api/v1/tasks                      # Create task manually
GET    /api/v1/tasks                      # List tasks (with filters)
GET    /api/v1/tasks/{id}                 # Get task detail
PUT    /api/v1/tasks/{id}                 # Update task
PUT    /api/v1/tasks/{id}/status          # Change task status
POST   /api/v1/tasks/{id}/approve         # Approve attorney/manager gated task
POST   /api/v1/tasks/{id}/request-changes # Send task back for revision
DELETE /api/v1/tasks/{id}                 # Delete task
POST   /api/v1/tasks/similar              # Suggest similar incomplete tasks before save

GET    /api/v1/transactions/{id}/tasks    # List tasks for a transaction
GET    /api/v1/property-workspaces/{id}/tasks # List tasks for a property workspace
POST   /api/v1/transactions/{id}/tasks/generate  # Generate tasks from use case + wizard data
POST   /api/v1/property-workspaces/{id}/tasks/generate # Generate prep/FSBO tasks
GET    /api/v1/transactions/{id}/closing-checklist # Generate printable checklist payload
```

#### Documents (`/api/v1/documents`)

```
POST   /api/v1/documents/upload           # Upload document(s)
POST   /api/v1/documents/intake           # Global drag/drop intake: classify, suggest name,
                                          #   locate transaction, suggest e-sign
GET    /api/v1/documents                  # List documents (with filters)
GET    /api/v1/documents/search           # Cross-transaction AI-assisted search
GET    /api/v1/documents/{id}             # Get document metadata
GET    /api/v1/documents/{id}/download    # Download/get signed URL
PUT    /api/v1/documents/{id}             # Update metadata (rename, reclassify)
POST   /api/v1/documents/{id}/approve     # Approve reviewed document
POST   /api/v1/documents/{id}/request-changes # Request revision / hold
DELETE /api/v1/documents/{id}             # Soft delete
PUT    /api/v1/documents/{id}/restore     # Restore soft-deleted
GET    /api/v1/documents/{id}/versions    # List version history

GET    /api/v1/transactions/{id}/documents # List documents for a transaction
GET    /api/v1/property-workspaces/{id}/documents # List documents for a property workspace
```

#### Share Links (`/api/v1/share-links`, `/api/v1/share`)

```
POST   /api/v1/share-links                # Create read-only milestone share link
GET    /api/v1/share-links                # List active/expired share links
GET    /api/v1/share-links/{id}           # Get link metadata + view stats
PUT    /api/v1/share-links/{id}           # Update expiry / recipient note
DELETE /api/v1/share-links/{id}           # Revoke link

GET    /api/v1/share/{token}              # Public read-only milestone timeline
```

#### Confidence Settings (`/api/v1/settings/confidence`)

```
GET    /api/v1/settings/confidence         # Get current settings
PUT    /api/v1/settings/confidence         # Update settings (Admin/TeamLead)
```

#### Audit Logs (`/api/v1/audit-logs`)

```
GET    /api/v1/audit-logs                  # List audit logs (Admin only)
GET    /api/v1/audit-logs/{entityType}/{entityId} # Logs for specific entity
```

#### Dashboard & Landing Experience (`/api/v1/dashboard`)

**Updated scope:** this section now covers role-specific dashboard landing
payloads plus the shared Active Transactions datasets used across internal
roles.

```
GET    /api/v1/dashboard/landing            # Role-aware landing contract; returns redirect target
GET    /api/v1/dashboard/agent-home         # Solo Agent dashboard payload
GET    /api/v1/dashboard/team-home          # Team Leader dashboard payload
GET    /api/v1/dashboard/attorney-home      # Attorney dashboard payload
GET    /api/v1/dashboard/fsbo-home          # FSBO dashboard payload

GET    /api/v1/dashboard/ai-briefing        # Topbar AI briefing for current role context
GET    /api/v1/dashboard/sidebar-kpis       # Shared shell KPI tiles
GET    /api/v1/dashboard/deal-state-counts  # Sidebar grouped nav counts
GET    /api/v1/dashboard/transaction-cards  # Shared Active Transactions card stack
GET    /api/v1/dashboard/attorney-queue     # Review-ready tasks/documents by urgency/state
GET    /api/v1/dashboard/fsbo-properties    # FSBO property cards and self-service milestones
```

**Notes:**
- `/dashboard/landing` is the canonical post-login entry point and resolves the
  correct role dashboard client-side route.
- `/dashboard/transaction-cards` remains the shared Active Transactions
  contract used by Agent, Team Lead, Attorney, and temporary FSBO transaction views.
- `/dashboard/attorney-queue` is optimized for legal review filters,
  approval status, and state-specific closing logic.
- `/dashboard/fsbo-home` and `/dashboard/fsbo-properties` focus on property
  workspaces first, with converted transactions appearing in the shared deal views.
- Sidebar navigation remains grouped as `Dashboard > Deals > Workflow > Intelligence`.

#### Health & System

```
GET    /api/v1/health                      # Health check
GET    /api/v1/health/ready                # Readiness check (DB connectivity)
```

### 3.3 Permission Matrix (Phase 1)

**Internal application roles**

| Capability | Admin | TeamLead | Agent | Elf | Attorney |
|------------|-------|----------|-------|-----|----------|
| User management | CRUD | Read team | Read self | Read self | Read self |
| Invite users | Yes | Team only | Own support users / invited collaborators | No | No |
| Create transaction | Yes | Yes | Yes | No | No |
| Create property workspace | Yes | Yes | Yes | Yes (assigned only) | No |
| View transactions | All | Team + personal | Own/assigned | Assigned | Assigned/review queue |
| View property workspaces | All | Team + personal | Own/assigned | Assigned | Assigned/review queue |
| Manage tasks | All | Team templates + oversight | Own txn/workspace | Assigned txn/workspace | Review-only unless explicitly assigned |
| Approve gated tasks/documents | Yes | Team policy overrides | No | No | Yes |
| Task templates | System-wide | Team-wide | Personal | No | Review only |
| Upload/view documents | All | Team | Own/assigned | Assigned | Assigned/review queue |
| Create/revoke share links | Yes | Team | Own/assigned | Assigned on behalf of owner | No |
| Dashboard landing data | All | Team + personal toggle | Own | Assigned | Attorney queue + assigned matters |
| Confidence settings | Global floor | Team threshold | No | No | No |
| Audit logs | Full | Team scope | No | No | Review actions only |

**External and token-based access**

| Capability | Client | FSBO | Vendor | Share Link Viewer |
|------------|--------|------|--------|-------------------|
| Full app login | Limited portal only | Yes, FSBO workspace only | No | No |
| View own milestones | Yes | Yes | No | Yes, read-only |
| Upload documents | Yes, portal-safe only | Yes, workspace-safe only | Yes, invited uploads only | No |
| Edit tasks | No | Limited self-service tasks only | No | No |
| View documents | Own portal-visible docs | Own portal-visible docs | Own uploads / requested docs | Timeline-safe only |
| View Active Transactions data | Own deal summary only | Converted deal summary only | No | No |
| Create share links | No | No | No | No |

---

## 4. Frontend UI/UX Design

### 4.1 Design System (Approved MVP Dashboard Set)

**Visual approach:** shared operations shell with dark grouped navigation and light content
surfaces plus role-tuned content modules. The approved MVP references are:
- `completed_designs/ve-active_transactions.html`
- `completed_designs/ve-homepage_dashboard-solo_agent.html`
- `completed_designs/ve-homepage_dashboard-team_leader.html`
- `completed_designs/ve-fsbo_dashboard.html`
- `completed_designs/ve-attorney_dashboard.html`

Files `ve-brandkit.txt` and `ve-style-sheet.txt` are explicitly ignored for
this design-system update.

- **Colors — brand-aligned semantic token system (CSS variables, white-label propagation):**
  ```css
  :root {
    --ve-orange: #e26812;
    --ve-orange-dark: #c85f13;
    --ve-slate: #2c4c7f;
    --ve-sidebar: #1e3356;
    --ve-sidebar-hover: #284168;
    --ve-bg: #f4f4f4;
    --ve-surface: #ffffff;
    --ve-border: #d9d9d6;
    --ve-text: #333333;
    --ve-success: #1a7a52;
    --ve-warning: #c07a0a;
    --ve-danger: #c8322f;
  }
  ```
  Status pills, urgency rails, milestone bars, and dashboard metric cards all
  derive from this token layer so white-label overrides remain centralized.
- **Typography:** IBM Plex Sans is the single application font across Agent,
  Team Leader, Attorney, FSBO, and Active Transactions experiences. IBM Plex
  Mono is reserved for numeric UI like currency, dates, IDs, countdowns, and
  badge counts.
- **Navigation language:** grouped sidebar structure is canonical for MVP:
  `Dashboard > Deals > Workflow > Intelligence`.
- **Layout:** one reusable shell with dark grouped sidebar, slim topbar, role
  dashboard hero zone, and high-density workspace cards/tables beneath.
- **Interaction rules:** 6px corner radius, clear urgency color hierarchy, and
  a minimum 48x48px interactive target size.
- **Components:** shadcn/ui primitives plus custom dashboard cards, grouped nav
  sections, transaction cards, attorney review rows, and FSBO property cards.
- **Responsive:** desktop-first, but all dashboards and the shared Active
  Transactions view must collapse cleanly to tablet/mobile without breaking the
  grouped nav or hiding approval/status cues.

### 4.2 Page Structure

**Scope update (2026-03-26):** the approved MVP now includes role-specific
dashboard landing pages for Solo Agent, Team Leader, Attorney, and FSBO, plus a
shared Active Transactions experience that all internal roles can flow into.

```text
App
|-- Auth (public)
|   |-- Login
|   |-- Register
|   |-- Forgot Password
|   |-- Reset Password
|   |-- OAuth Callback
|   `-- Invite Accept
|
|-- Onboarding (protected, standalone)
|   `-- OnboardingWizard
|
|-- Main App (protected)
|   |-- Topbar
|   |   |-- Global search
|   |   |-- Today's AI Briefing
|   |   |-- Notifications
|   |   `-- Profile menu
|   |
|   |-- Sidebar
|   |   |-- Dashboard
|   |   |   |-- Role Landing
|   |   |   |-- Personal Metrics
|   |   |   `-- Team / Queue / FSBO summaries
|   |   |-- Deals
|   |   |   |-- Active Transactions
|   |   |   |-- Pending
|   |   |   |-- Closed
|   |   |   `-- All Transactions
|   |   |-- Workflow
|   |   |   |-- Task Queue
|   |   |   |-- Closing Calendar
|   |   |   `-- All Documents
|   |   |-- Intelligence
|   |   |   |-- AI Suggestions
|   |   |   `-- Analytics
|   |   |-- Pinned CTA
|   |   |   |-- New Transaction
|   |   |   `-- New Property Workspace
|   |   `-- User profile summary
|   |
|   |-- Role Dashboards
|   |   |-- Solo Agent Dashboard
|   |   |-- Team Leader Dashboard
|   |   |-- Attorney Dashboard
|   |   `-- FSBO Dashboard
|   |
|   |-- Shared Active Transactions Workspace
|   |   |-- Agent / Elf personal view
|   |   |-- Team Lead team/personal toggle
|   |   `-- Attorney assigned-matter view
|   |
|   |-- Transaction Detail
|   |   |-- Overview
|   |   |-- Tasks
|   |   |-- Documents
|   |   |-- Parties
|   |   `-- Communications
|   |
|   |-- Property Workspace Detail
|   |   |-- Overview
|   |   |-- Prep Tasks
|   |   |-- Documents
|   |   |-- Timeline
|   |   `-- Convert to Transaction
|   |
|   |-- Public Share Timeline
|   |   `-- Read-only milestone view
|   |
|   |-- Supporting workspaces
|   |   |-- Task Queue
|   |   |-- Closing Calendar
|   |   |-- All Documents
|   |   |-- Contacts
|   |   `-- Analytics
|   |
|   |-- Profile
|   |   |-- Personal Info
|   |   |-- Notification Preferences
|   |   |-- Checklist Templates
|   |   `-- Integrations
|   |
|   `-- Admin
|       |-- User Management
|       |-- Task Templates
|       |-- Confidence Settings
|       |-- Tenant/Brokerage Settings
|       `-- Audit Logs
|
`-- External Experiences
    |-- Client Portal (transaction-focused)
    |-- FSBO Workspace (property-focused)
    `-- Share Link Timeline (read-only)
```

### 4.3 Key UI Components (Phase 1)

#### 4.3.1 Shared Application Shell

- Shared left sidebar with grouped navigation, KPI/summary modules, and pinned
  primary actions.
- Shared topbar with greeting, AI briefing, notifications, search, and profile.
- Role-aware header region that swaps in Solo Agent, Team Leader, Attorney, or
  FSBO-specific summary cards without changing the base shell.
- Common modal/overlay system for add task, upload document, document search,
  share-link creation, and review actions.
- One visual language for urgency, milestone progress, approval state, and
  customer-safe visibility across all role dashboards and deal/workspace views.

#### 4.3.1b Role Dashboard Modules

- **Solo Agent dashboard:** personal pipeline metrics, urgent follow-ups,
  upcoming closings, and shortcuts into Active Transactions.
- **Team Leader dashboard:** personal/team toggle, team workload snapshots,
  assignee-aware pipeline visibility, and oversight shortcuts.
- **Attorney dashboard:** review queue, state-specific closing items,
  approval-needed documents/tasks, and legal-status filters.
- **FSBO dashboard:** property-centric status cards, self-service milestones,
  document prompts, and guidance steps before transaction conversion.

#### 4.3.2 Transaction and Property Detail Views

- Transaction detail remains a tabbed operations view for active deals.
- Property workspace detail mirrors the same pattern but emphasizes prep tasks,
  timeline guidance, documents, and conversion-to-transaction actions.

```
┌─────────────────────────────────────────────────────────────┐
│  ← Back   123 Main Street, Indianapolis IN 46220           │
│  Buy-Fin  |  $350,000  |  Closing: Apr 15, 2026            │
│  Status: Active                              [Edit] [...]   │
├─────────────────────────────────────────────────────────────┤
│  [Overview] [Tasks] [Documents] [Parties] [Communications]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tasks (24 total)                                           │
│  ┌─ Filter: [All ▾] [By Status ▾] [By Vendor ▾] ────────┐  │
│  │                                                       │  │
│  │  ✓ Contract Acceptance Date        Mar 1    Complete   │  │
│  │  ✓ Review Documentation            Mar 1    Complete   │  │
│  │  ✓ Buyer Welcome (Automated)       Mar 1    Complete   │  │
│  │  ○ Loan Officer Welcome            Mar 4    Pending    │  │
│  │  ○ Order Title                     Mar 4    Pending    │  │
│  │  ○ Request HOA Docs                Mar 8    Pending    │  │
│  │  ○ Insurance Reminder              Mar 15   Upcoming   │  │
│  │  ...                                                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### 4.3.3 Admin and Template Management

```
┌─────────────────────────────────────────────────────────────┐
│  Task Templates                    [Import CSV] [+ New]     │
├─────────────────────────────────────────────────────────────┤
│  Filter: [All Use Cases ▾]  [All Categories ▾]  [Search]    │
├─────────────────────────────────────────────────────────────┤
│  ID │ Name                      │ Use Cases    │ Target     │
│  ───┼───────────────────────────┼──────────────┼────────────│
│   8 │ Review Documentation      │ All          │ Agent      │
│  10 │ Buyer Welcome (Automated) │ Buy-Fin/Cash │ Buyer      │
│  20 │ Seller Welcome (Automated)│ Sell-Fin/Cash│ Seller     │
│  30 │ Co-op Agent Welcome       │ All          │ Co-op Agent│
│  50 │ Pending Reminder          │ Sell-Fin/Cash│ Agent      │
│  60 │ Loan Officer Welcome      │ Buy/Sell-Fin │ Loan Officer│
│  ...│                           │              │            │
├─────────────────────────────────────────────────────────────┤
│  ← Click row to edit template with dependency configuration │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 New Routes (Phase 1)

```typescript
export const ROUTES = {
  // Auth (existing)
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  OAUTH_CALLBACK: '/auth/callback',
  ONBOARDING: '/onboarding',
  INVITE_ACCEPT: '/invite/:token',          // NEW

  // Main app - role-aware dashboard and grouped sidebar navigation
  DASHBOARD: '/dashboard',
  DASHBOARD_AGENT: '/dashboard/agent',
  DASHBOARD_TEAM_LEAD: '/dashboard/team-lead',
  DASHBOARD_ATTORNEY: '/dashboard/attorney',
  DASHBOARD_FSBO: '/dashboard/fsbo',
  PROFILE: '/profile',

  // Deals section
  ACTIVE_TRANSACTIONS: '/transactions/active',
  PENDING_TRANSACTIONS: '/transactions/pending',
  CLOSED_TRANSACTIONS: '/transactions/closed',
  ALL_TRANSACTIONS: '/transactions/all',
  ACTIVE_DEALS: '/deals',                    // alias / legacy naming
  TRANSACTIONS: '/transactions',             // backward-compatible base route
  NEW_TRANSACTION: '/transactions/new',
  TRANSACTION_DETAIL: '/transactions/:id',
  PROPERTY_WORKSPACES: '/properties',
  PROPERTY_WORKSPACE_DETAIL: '/properties/:id',

  // Workflow section
  TASK_QUEUE: '/tasks/queue',
  CLOSING_CALENDAR: '/closing-calendar',
  DOCUMENTS: '/documents',
  ALL_DOCUMENTS: '/documents/all',
  ATTORNEY_REVIEW: '/attorney/review/:taskId',
  ATTORNEY_STATE_RULES: '/attorney/state-rules',

  // Existing/future task views
  DEADLINES: '/deadlines',                   // future dashboard/deadline page
  TASKS: '/tasks',                           // cross-transaction task view
  TASK_DETAIL: '/tasks/:id',
  
  // Intelligence / utility section
  AI_SUGGESTIONS: '/ai-suggestions',
  ANALYTICS: '/analytics',
  SETTINGS: '/settings',

  // Supporting pages retained in overall app shell
  CONTACTS: '/contacts',
  CONTACT_DETAIL: '/contacts/:id',
  MESSAGES: '/messages',
  PIPELINE: '/pipeline',
  SHARE_TIMELINE: '/share/:token',

  // Admin
  ADMIN_USERS: '/admin/users',              // NEW
  ADMIN_USER_DETAIL: '/admin/users/:userId',
  ADMIN_TEMPLATES: '/admin/task-templates',  // NEW
  ADMIN_TEMPLATE_DETAIL: '/admin/task-templates/:id', // NEW
  ADMIN_TEMPLATE_IMPORT: '/admin/task-templates/import', // NEW
  ADMIN_CONFIDENCE: '/admin/confidence',     // NEW
  ADMIN_AUDIT_LOGS: '/admin/audit-logs',     // NEW
  ADMIN_TENANT: '/admin/tenant',             // NEW
} as const;
```

### 4.5 Frontend State Architecture

```text
React Query (TanStack Query)
|-- Server State (cached via React Query)
|   |-- /auth/me                      -> current user
|   |-- /dashboard/landing            -> role-aware dashboard target
|   |-- /dashboard/agent-home         -> solo agent landing data
|   |-- /dashboard/team-home          -> team leader landing data
|   |-- /dashboard/attorney-home      -> attorney landing data
|   |-- /dashboard/fsbo-home          -> FSBO landing data
|   |-- /dashboard/ai-briefing        -> topbar AI briefing counts
|   |-- /dashboard/sidebar-kpis       -> grouped-shell KPI tiles
|   |-- /dashboard/deal-state-counts  -> Active/Pending/Closed/All counts
|   |-- /dashboard/transaction-cards  -> shared Active Transactions card data
|   |-- /dashboard/attorney-queue     -> review queue
|   |-- /dashboard/fsbo-properties    -> property workspace cards
|   |-- /transactions                 -> transaction list
|   |-- /property-workspaces          -> property workspace list/detail
|   |-- /tasks                        -> task list
|   |-- /contacts                     -> contact directory
|   |-- /documents                    -> transaction documents
|   |-- /documents/search             -> all-documents AI search
|   |-- /share-links                  -> active/expired timeline links
|   |-- /task-templates               -> template library
|   `-- /audit-logs                   -> audit trail
|
|-- Client State (React Context)
|   |-- AuthContext                   -> JWT token, user session
|   |-- ThemeContext                  -> white-label branding
|   |-- RoleDashboardContext          -> role landing composition + dashboard mode
|   |-- WorkspaceViewContext          -> Team Lead personal/team toggle
|   |-- WorkspaceFilterContext        -> deal-state + page-tab filters
|   |-- FsboWorkspaceContext          -> property workspace progress + guidance state
|   |-- AttorneyReviewContext         -> review queue filters + approval actions
|   |-- ShareLinkContext              -> create/revoke link state
|   |-- GlobalDropzoneContext         -> workspace-wide document drop handling
|   `-- NotificationContext           -> toast/alert state
|
`-- Form State (React Hook Form)
    |-- TransactionForm
    |-- PropertyWorkspaceForm
    |-- TaskTemplateForm
    |-- ContactForm
    |-- ShareLinkForm
    |-- AttorneyReviewForm
    `-- UserInviteForm
```

---

## 5. Phase 1 Implementation Plan

### 5.1 Milestone 1.1 — Project Setup & Architecture Design (Week 1)

**Deliverables:**

- [x] Review existing codebase (FastAPI + React scaffolding exists)
- [ ] Finalize this system design document
- [ ] Update database schema (new migration file)
- [ ] Update API endpoint documentation (OpenAPI/Swagger)
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Set up staging environment on AWS EC2
- [ ] Configure branching strategy (main → develop → feature branches)

**Backend tasks:**
1. Create new migration: `supabase/migrations/20260305_phase1_schema.sql`
   - Add `tenants` table
   - Add `teams` table
   - Add `contacts` table
   - Add `property_workspaces` table
   - Update `users` table (new columns)
   - Update `transactions` table (expanded fields + `property_workspace_id` + attorney fields)
   - Add `transaction_assignments` table
   - Add `transaction_parties` table
   - Add `task_templates` table
   - Update `tasks` table (workspace context + approval fields)
   - Update `documents` table (workspace context + review/portal fields)
   - Update `communication_logs` table (workspace context + visibility)
   - Add `milestone_share_links` table
   - Add `audit_logs` table
   - Add `invitation_tokens` table
   - Add `confidence_settings` table
   - Create RLS policies
   - Create updated_at triggers

2. Update domain models:
   - `app/models/tenant.py` (new)
   - `app/models/team.py` (new)
   - `app/models/contact.py` (new)
   - `app/models/property_workspace.py` (new)
   - `app/models/task_template.py` (new)
   - `app/models/transaction_party.py` (new)
   - `app/models/communication_log.py` (new)
   - `app/models/milestone_share_link.py` (new)
   - `app/models/audit_log.py` (new)
   - `app/models/invitation.py` (new)
   - Update `app/models/enums.py` (new enums)
   - Update `app/models/user.py` (new fields)
   - Update `app/models/transaction.py` (expanded fields)
   - Update `app/models/task.py` (workspace + approval fields)
   - Update `app/models/document.py` (workspace, review, portal visibility)

3. Update Pydantic schemas:
   - New schema files for each new model
   - Update existing schemas for expanded fields

**Frontend tasks:**
1. Update route constants for role dashboards, property workspaces, attorney review, and share timelines
2. Define dashboard composition strategy for Agent, Team Leader, Attorney, and FSBO views
3. Plan shared shell components and grouped sidebar navigation

### 5.2 Milestone 1.2 — Database & Data Model Implementation (Week 2)

**Deliverables:**

- [ ] Run migration in Supabase
- [ ] Implement all repositories for new tables
- [ ] Import task catalogue from CSV
- [ ] Set up Supabase storage buckets
- [ ] Document all API endpoints (Swagger auto-generated)

**Backend tasks:**
1. New repositories:
   - `app/repositories/tenant_repository.py`
   - `app/repositories/team_repository.py`
   - `app/repositories/contact_repository.py`
   - `app/repositories/property_workspace_repository.py`
   - `app/repositories/task_template_repository.py`
   - `app/repositories/transaction_party_repository.py`
   - `app/repositories/transaction_assignment_repository.py`
   - `app/repositories/communication_log_repository.py`
   - `app/repositories/share_link_repository.py`
   - `app/repositories/audit_log_repository.py`
   - `app/repositories/invitation_repository.py`
   - `app/repositories/confidence_repository.py`
   - Update existing repositories for new columns

2. CSV import service:
   - `app/services/task_import_service.py`
   - Parse REWORKING_TASK_DB.csv
   - Map columns to `task_templates` fields
   - Handle special cases (Both behavior, wizard references, conditions)
   - Create import API endpoint

3. Storage setup:
   - Configure buckets: `documents`, `avatars`, `logos`, `property-assets`
   - Set bucket policies for access control
   - Validate portal-safe and share-link-safe asset access paths

### 5.3 Milestone 1.3 — Authentication & User Management Backend (Week 3)

**Deliverables:**

- [ ] Supabase Auth integration (already partially done)
- [ ] Registration, login, password reset APIs (already partially done)
- [ ] Invite-based onboarding flow
- [ ] RBAC system with 8 roles (already partially done)
- [ ] Permission middleware (already partially done)
- [ ] Contact management API
- [ ] Property workspace and share-link permission APIs
- [ ] Confidence threshold settings API
- [ ] Unit tests

**Backend tasks:**
1. Invitation system:
   - `app/services/invitation_service.py`
   - Generate secure tokens
   - Send invitation emails (via Supabase or custom SMTP)
   - Token validation and acceptance flow
   - Role assignment on acceptance

2. Enhanced RBAC:
   - Update `app/core/auth.py` with expanded permission checks
   - Add team-level permission checks
   - Add transaction-level permission checks (is user assigned?)
   - Add property-workspace permission checks
   - Add attorney approval and review permissions

3. Contact management:
   - `app/services/contact_service.py`
   - `app/api/v1/contacts.py`
   - CRUD with PII encryption
   - Search functionality
   - Vendor card feature (generate shareable link)

4. Property workspace and share links:
   - `app/services/property_workspace_service.py`
   - `app/api/v1/property_workspaces.py`
   - `app/services/share_link_service.py`
   - `app/api/v1/share_links.py`
   - Public timeline token validation + expirable read-only access

5. Confidence settings:
   - `app/services/confidence_service.py`
   - `app/api/v1/confidence.py`
   - Admin sets global floor
   - Team Lead sets team thresholds (validated >= admin floor)
   - Add attorney-review and customer-visible overrides

6. Audit logging service:
   - `app/services/audit_service.py`
   - Middleware or decorator for automatic audit logging
   - Before/after state capture

7. Tests:
   - Auth flow tests (expand existing)
   - Invitation flow tests
   - RBAC permission tests (expand existing)
   - Contact CRUD tests
   - Confidence settings tests
   - Share-link permission tests
   - Attorney review workflow tests

---

## Appendix A: Task Template Import Mapping

Detailed mapping from REWORKING_TASK_DB.csv to `task_templates`:

| Task Name | ID | use_cases | target | dep_rel | dep_task_id | float | conditions | both_behavior |
|-----------|----|-----------|---------|---------|----|-------|------------|---------------|
| Contract Acceptance Date | 5 | all | - | - | - | - | - | - |
| Review Documentation | 8 | all 4 | Agent | FS | 5 | 0 | - | single_instance |
| Buyer Welcome | 10 | Buy-Fin,Buy-Cash | Buyer | FS | 5 | 0 | - | - |
| Seller Welcome | 20 | Sell-Fin,Sell-Cash | Seller | FS | 5 | 0 | - | - |
| Co-op Agent Welcome | 30 | all 4 | Co-op Agent | FS | 5 | 0 | - | skip |
| Pending Reminder | 50 | Sell-Fin,Sell-Cash | Agent | FS | 5 | 3 | - | single_instance |
| Loan Officer Welcome | 60 | Buy-Fin,Sell-Fin | Loan Officer | FS | 5 | 0 | - | single_instance |
| Order Title | 70 | all 4 | Title | FS | 5 | 0 | wizard:title_ordered_by=us | single_instance |
| Confirm Title Order | 80 | all 4 | Title | FS | 5 | 0 | wizard:title_ordered_by=us | - |
| Request HOA Docs | 90 | Buy-Fin,Buy-Cash | Co-op Agent | FS | 110 | -5 | wizard:has_hoa=true | skip |
| Request HOA Docs | 95 | all 4 | Seller | FS | 115 | -5 | wizard:has_hoa=true | replace_90_100 |
| Request HOA Docs | 100 | Sell-Fin,Sell-Cash | Seller | FS | 120 | -5 | wizard:has_hoa=true | skip |
| Deliver HOA Docs | 110 | Buy-Fin,Buy-Cash | Buyer | FS | 5 | wizard:hoa_doc_days | wizard:has_hoa=true | skip |
| Deliver HOA Docs | 115 | all 4 | Buyer | FS | 5 | wizard:hoa_doc_days | wizard:has_hoa=true | replace_110_120 |
| Deliver HOA Docs | 120 | Sell-Fin,Sell-Cash | Co-op Agent | FS | 5 | wizard:hoa_doc_days | wizard:has_hoa=true | skip |
| Closing Date | 1000 | all | - | - | - | wizard:closing_date | - | - |

*(Full mapping for all 50+ tasks follows the same pattern)*

## Appendix B: Migration from Current Schema

The current schema has:
- `users`: basic fields → needs new columns (bio, avatar, notification_prefs, team_id)
- `transactions`: minimal fields → needs full expansion
- `tasks`: basic fields → needs template_id, target, AI fields
- `documents`: basic fields → needs versioning, classification, signature tracking
- `integrations`: adequate for Phase 1
- Missing: tenants, teams, contacts, task_templates, transaction_assignments, transaction_parties, communication_logs, audit_logs, invitation_tokens, confidence_settings
- `property_workspaces`: new table needed for FSBO and pre-transaction listing prep
- `transactions`: must also link back to property workspaces and store attorney-closing context
- `tasks`, `documents`, and `communication_logs`: must support both transaction and property-workspace contexts
- `milestone_share_links`: new table needed for expirable read-only timeline sharing

Migration strategy:
1. New migration adds all new tables with `IF NOT EXISTS`
2. `ALTER TABLE` adds new columns to existing tables with defaults
3. Existing data is preserved — no destructive changes
4. Run CSV import after migration to populate `task_templates`
5. Apply RLS policies after data migration
6. Add token-validation guards for public share timelines after RLS is in place

## Appendix C: ListedKit Feature Alignment

| ListedKit Feature | Velvet Elves Equivalent | Phase |
|-------------------|------------------------|-------|
| Contract upload + AI parse | Wizard (document-first approach) | 3 |
| Smart timeline generation | Task engine with dependency/float logic | 2 |
| Deadline tracking | Task due dates + notifications | 2 |
| Calendar sync | Google Calendar/Outlook integration | 6 |
| Compliance checking | Document review + signature tracking | 3 |
| Email drafting | AI email engine | 4 |
| Team collaboration | RBAC + transaction assignments | 1 |
| Transaction intake wizard | The Wizard (AI-driven) | 3 |
| Per-intake pricing | Stripe payment integration | 5 |
| Multi-state support | State-based task rules | 2 |

Key differentiators from ListedKit:
- **More granular roles** (8 internal/external roles vs ListedKit's simpler model)
- **AI email automation** with safeguards (ListedKit has basic drafting)
- **Attorney approval guardrails** for legal-sensitive work
- **FSBO property workspace** before a transaction formally exists
- **Vendor communication system** with structured responses
- **White-label multi-tenancy** (ListedKit is single-brand)
- **Advertising module** for monetization
- **Task dependency engine** (more sophisticated than ListedKit's checklists)
