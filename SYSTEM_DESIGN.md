# Velvet Elves - System Design Document

**Date:** 2026-03-05
**Last Updated:** 2026-03-30 (Active Transactions UI alignment — key dates, modals, transaction history, AI chat)
**Scope:** Phase 1 (Milestones 1.1, 1.2, 1.3) — scalable for all future phases; dashboard and workspace designs approved for Solo Agent, Team Leader, Attorney, FSBO, and shared Active Transactions; Active Transactions UI fully aligned with ve-active_transactions.html
**Reference:** ListedKit.com functionality as design benchmark

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

### 1.4 Multi-Tenant Architecture

```
Tenant (Brokerage)
  └── Users (Agent, Elf, TeamLead, Attorney, Admin, Client, FSBO_Customer, Vendor)
       └── Transactions
            ├── Tasks
            ├── Documents
            ├── Contacts
            └── Communication Logs
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
  │    ├── transactions ──┬── transaction_tasks     │
  │    │    │             ├── transaction_documents  │
  │    │    │             ├── transaction_contacts   │
  │    │    │             ├── transaction_parties    │
  │    │    │             └── communication_logs     │
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
  role                   TEXT NOT NULL DEFAULT 'Agent',    -- Agent,Elf,TeamLead,Attorney,Admin,
                                                         -- Client,FSBO_Customer,Vendor
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
                                                   -- 'attorney','buyer','seller','inspector',
                                                   -- 'appraiser','home_warranty','other'
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

#### 2.2.5 `transactions` — Real estate deals (UPDATED)

```sql
CREATE TABLE IF NOT EXISTS public.transactions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL REFERENCES public.tenants(id),
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
  purchase_price        NUMERIC(12,2),
  earnest_money         NUMERIC(12,2),

  -- Core dates
  contract_acceptance_date DATE,
  closing_date             DATE,
  closing_time             TIME,                          -- time-of-day for closing (NULL = TBD)
  possession_date          DATE,
  possession_time          TIME,                          -- time-of-day for possession (NULL = TBD)

  -- Key milestone dates (editable from Active Transactions drawer)
  em_delivered_date        DATE,                          -- Earnest Money delivered
  inspection_response_date DATE,                         -- Inspection response deadline
  appraisal_expected_date  DATE,                         -- Appraisal expected
  cd_delivered_date        DATE,                          -- Closing Disclosure delivered
  cleared_to_close_date    DATE,                         -- Cleared to Close

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

  -- Closing mode (attorney vs title/escrow)
  closing_mode            TEXT,                           -- 'attorney','title_escrow','shared_approval'
                                                         -- NULL if not yet determined

  -- Financing specific
  is_owner_occupied       BOOLEAN DEFAULT TRUE,

  -- FSBO / listing-prep state
  is_fsbo                 BOOLEAN DEFAULT FALSE,          -- true for FSBO customer-owned properties
  fsbo_state              TEXT,                           -- 'listing_prep','under_contract',NULL
                                                         -- supports property-centric pre-contract state

  -- Status
  status                  TEXT NOT NULL DEFAULT 'Active',
  notes                   TEXT,
  wizard_completed        BOOLEAN DEFAULT FALSE,

  -- Metadata
  metadata_json           JSONB DEFAULT '{}'::jsonb,    -- extensible fields
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_transactions_tenant_id ON public.transactions (tenant_id);
CREATE INDEX idx_transactions_created_by ON public.transactions (created_by);
CREATE INDEX idx_transactions_status ON public.transactions (status);
CREATE INDEX idx_transactions_closing_date ON public.transactions (closing_date);
CREATE INDEX idx_transactions_use_case ON public.transactions (use_case);
```

**Major changes from current:**
- Expanded from 4 fields to full transaction model matching requirements
- `use_case` now maps to 6 types: `Buy-Fin`, `Buy-Cash`, `Sell-Fin`, `Sell-Cash`, `Both-Fin`, `Both-Cash`
- Added all wizard-derived fields: inspection, HOA, home warranty, title, insurance, financing
- Added `representation_type` and `financing_type` as separate fields
- `user_id` renamed to `created_by` for clarity
- Property address split into components (city, state, zip, county)
- Added `closing_mode` for attorney closing vs title/escrow vs shared approval
- Added `is_fsbo` and `fsbo_state` for FSBO customer property-centric workflows
- Added key milestone date columns (`em_delivered_date`, `inspection_response_date`,
  `appraisal_expected_date`, `cd_delivered_date`, `cleared_to_close_date`) — these are
  the editable "Key Dates" shown in the Active Transactions expanded drawer
- Added `closing_time` and `possession_time` (TIME) for time-of-day tracking
  (displayed as "Time: TBD" until set)
- `metadata_json` for extensibility without schema changes

#### 2.2.6 `transaction_assignments` — Who works on a transaction (NEW)

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

**Why:** Requirement 2.3 — transactions can be assigned to elf, agent, or attorney; support reassignment and multiple participants.

#### 2.2.7 `transaction_parties` — External parties on a deal (NEW)

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

#### 2.2.8 `task_templates` — Master task library (NEW)

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
                                                                 -- 'Title','Home Warranty Company',etc.
  cc_targets          TEXT[],                                     -- CC recipients
  milestone_label     TEXT,                                       -- 'Offer Accepted','Title Work Ordered',
                                                                 -- 'Inspection Scheduled', etc.
  -- Use case applicability (which of the 6 transaction types)
  use_cases           TEXT[] NOT NULL DEFAULT '{}',               -- e.g. {'Buy-Fin','Buy-Cash'}

  -- Dependency configuration
  dep_rel             TEXT DEFAULT 'FS',                          -- 'FS' (Finish-Start) or 'SS' (Start-Start)
  dep_task_id         INTEGER,                                   -- legacy task ID this depends on
  float_days          TEXT,                                       -- can be integer or formula ref
                                                                 -- e.g. '0', '14', 'wizard:hoa_doc_days'

  -- Automation
  automation_level    TEXT NOT NULL DEFAULT 'Manual',             -- 'Automated','ToBeAutomated','Manual'

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
```

**Why:** This is the most critical table. It imports the 50+ tasks from REWORKING_TASK_DB.csv and makes them configurable. Key design decisions:
- `legacy_task_id` preserves the original task ID numbering for dependency references
- `dep_rel` captures FS (Finish-Start) vs SS (Start-Start) relationships
- `float_days` can be a number OR a wizard field reference (e.g., "wizard:hoa_doc_days")
- `conditions_json` encodes wizard-dependent logic (e.g., "only if inspection=yes")
- `both_rep_behavior` handles the "Both" representation special cases
- Supports system-wide (tenant_id=NULL), per-tenant, and per-team templates
- Team leads can override templates for their team; agents own personal templates

#### 2.2.9 `tasks` — Transaction-specific task instances (UPDATED)

```sql
CREATE TABLE IF NOT EXISTS public.tasks (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id    UUID NOT NULL REFERENCES public.transactions(id) ON DELETE CASCADE,
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

  -- AI recommendation tracking
  source            TEXT DEFAULT 'template',           -- 'template','ai_recommended','manual'
  ai_reason         TEXT,                              -- why AI recommended this task
  ai_confidence     REAL,                              -- confidence score 0-1

  -- Ordering and metadata
  sort_order        INTEGER NOT NULL DEFAULT 0,
  notes             TEXT,
  metadata_json     JSONB DEFAULT '{}'::jsonb,

  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tasks_transaction_id ON public.tasks (transaction_id);
CREATE INDEX idx_tasks_template_id ON public.tasks (template_id);
CREATE INDEX idx_tasks_status ON public.tasks (status);
CREATE INDEX idx_tasks_due_date ON public.tasks (due_date);
CREATE INDEX idx_tasks_target ON public.tasks (target);
```

**Major changes from current:**
- Added `template_id` linking back to source template
- Added `target`, `cc_targets`, `milestone_label` from task DB
- Added `completion_method` so manual tasks align with the new Add Task flow
- `due_date` is now proper DATE (was TEXT)
- Added `completed_at` timestamp
- `dependencies_json` is now JSONB (was TEXT)
- Added AI recommendation fields (`source`, `ai_reason`, `ai_confidence`)
- Added `notes` for task-specific annotations

#### 2.2.10 `documents` — Uploaded files (UPDATED)

```sql
CREATE TABLE IF NOT EXISTS public.documents (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES public.tenants(id),
  transaction_id    UUID REFERENCES public.transactions(id) ON DELETE SET NULL,
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
                                                      -- 'inspection_report','hoa_docs',
                                                      -- 'closing_disclosure','utility_info',
                                                      -- 'sellers_disclosure','blc_tax_sheet',
                                                      -- 'earnest_money','other'
  doc_label         TEXT,                              -- user-friendly display label

  -- Version control
  version           INTEGER NOT NULL DEFAULT 1,
  parent_id         UUID REFERENCES public.documents(id),  -- previous version
  is_current        BOOLEAN DEFAULT TRUE,
  is_legacy         BOOLEAN DEFAULT FALSE,            -- marked as outdated by vendor re-upload

  -- Status
  status            TEXT NOT NULL DEFAULT 'pending',   -- pending,processed,failed,archived
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
CREATE INDEX idx_documents_uploaded_by ON public.documents (uploaded_by);
CREATE INDEX idx_documents_type ON public.documents (doc_type);
CREATE INDEX idx_documents_parent ON public.documents (parent_id);
```

**Changes from current:**
- Added version control (`version`, `parent_id`, `is_current`, `is_legacy`)
- Added document classification (`doc_type`, `doc_label`)
- Added soft delete fields
- Added AI extraction storage (`ai_extracted_data`, `ai_confidence`)
- Added signature tracking fields
- Renamed `user_id` to `uploaded_by`

#### 2.2.11 `communication_logs` — Immutable communication record (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.communication_logs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES public.tenants(id),
  transaction_id    UUID REFERENCES public.transactions(id) ON DELETE SET NULL,

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
CREATE INDEX idx_comm_logs_sender ON public.communication_logs (sender_user_id);
CREATE INDEX idx_comm_logs_channel ON public.communication_logs (channel);
CREATE INDEX idx_comm_logs_created ON public.communication_logs (created_at);
```

**Why:** Requirement 6.1 — immutable unified communication log. Every email, system message, document action, and AI send is recorded. No `updated_at` because rows are immutable.

#### 2.2.12 `audit_logs` — System-wide audit trail (NEW)

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
  entity_type     TEXT NOT NULL,                       -- 'transaction','task','document',
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

**Why:** Requirement 10.3 — every action logged with user, role, timestamp, before/after state, and human-readable summary.

#### 2.2.13 `invitation_tokens` — Invite-based onboarding (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.invitation_tokens (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES public.tenants(id),
  invited_by      UUID NOT NULL REFERENCES public.users(id),
  email           TEXT NOT NULL,                       -- Fernet encrypted
  role            TEXT NOT NULL DEFAULT 'Agent',
  team_id         UUID REFERENCES public.teams(id),
  transaction_id  UUID REFERENCES public.transactions(id),  -- if invited to a specific transaction
  token           TEXT NOT NULL UNIQUE,
  expires_at      TIMESTAMPTZ NOT NULL,
  used_at         TIMESTAMPTZ,
  is_used         BOOLEAN DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_invitations_token ON public.invitation_tokens (token);
CREATE INDEX idx_invitations_tenant ON public.invitation_tokens (tenant_id);
```

**Why:** Requirement 1.1 — invitation tokens sent via email for onboarding.

#### 2.2.14 `confidence_settings` — AI confidence thresholds (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.confidence_settings (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID REFERENCES public.tenants(id),
  team_id               UUID REFERENCES public.teams(id),

  -- Global settings (admin-controlled)
  global_min_floor      REAL DEFAULT 0.75,             -- minimum confidence for any auto-action
  auto_proceed_threshold REAL DEFAULT 0.90,            -- "ship it" tier
  review_threshold      REAL DEFAULT 0.75,             -- "I better see it first" tier

  -- Task-specific overrides
  task_overrides_json   JSONB DEFAULT '{}'::jsonb,     -- {"task_category": {"threshold": 0.85}}

  created_by            UUID REFERENCES public.users(id),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (tenant_id, team_id)
);
```

**Why:** Requirement 4.7 — two-tiered confidence system configurable per team, with admin global minimum floor.

#### 2.2.15 `integrations` — Email/OAuth connections (EXISTING, no changes)

Already in the schema. No changes needed for Phase 1.

### 2.3 Updated Enums

```python
class UserRole(str, enum.Enum):
    AGENT = "Agent"
    ELF = "Elf"
    TEAM_LEAD = "TeamLead"
    ATTORNEY = "Attorney"          # NEW: legal review, packet release, state-rule compliance
    ADMIN = "Admin"
    CLIENT = "Client"
    FSBO_CUSTOMER = "FSBO_Customer" # NEW: self-guided seller workspace
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

class TaskStatus(str, enum.Enum):
    PENDING = "Pending"
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"
    BLOCKED = "Blocked"
    SKIPPED = "Skipped"

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
    INSPECTION_REPORT = "inspection_report"
    HOA_DOCS = "hoa_docs"
    CLOSING_DISCLOSURE = "closing_disclosure"
    UTILITY_INFO = "utility_info"
    SELLERS_DISCLOSURE = "sellers_disclosure"
    BLC_TAX_SHEET = "blc_tax_sheet"
    EARNEST_MONEY = "earnest_money"
    HOME_WARRANTY = "home_warranty"
    INSURANCE = "insurance"
    OTHER = "other"

class ContactType(str, enum.Enum):
    CO_AGENT = "co_agent"
    LOAN_OFFICER = "loan_officer"
    TITLE_REP = "title_rep"
    ATTORNEY = "attorney"          # NEW: closing attorney / settlement attorney
    BUYER = "buyer"
    SELLER = "seller"
    INSPECTOR = "inspector"
    APPRAISER = "appraiser"
    HOME_WARRANTY = "home_warranty"
    OTHER = "other"

class CommunicationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"                    # NEW: future SMS provider integration
    VOICE_CALL = "voice_call"      # NEW: future click-to-call / call-bridge
    PUSH = "push"                  # NEW: push notifications
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
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.communication_logs ENABLE ROW LEVEL SECURITY;
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

-- Similar policies for all other tables...
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

#### Transactions (`/api/v1/transactions`)

```
POST   /api/v1/transactions               # Create transaction
GET    /api/v1/transactions               # List transactions (filtered by role)
GET    /api/v1/transactions/{id}          # Get transaction detail
PUT    /api/v1/transactions/{id}          # Update transaction
DELETE /api/v1/transactions/{id}          # Soft delete transaction
PUT    /api/v1/transactions/{id}/status   # Change status
PUT    /api/v1/transactions/{id}/use-case # Change use case (targeted task update)

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
```

#### Tasks (`/api/v1/tasks`)

```
POST   /api/v1/tasks                      # Create task manually
GET    /api/v1/tasks                      # List tasks (with filters)
GET    /api/v1/tasks/{id}                 # Get task detail
PUT    /api/v1/tasks/{id}                 # Update task
PUT    /api/v1/tasks/{id}/status          # Change task status
DELETE /api/v1/tasks/{id}                 # Delete task
POST   /api/v1/tasks/similar              # Suggest similar incomplete tasks before save

GET    /api/v1/transactions/{id}/tasks    # List tasks for a transaction
POST   /api/v1/transactions/{id}/tasks/generate  # Generate tasks from use case + wizard data
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
DELETE /api/v1/documents/{id}             # Soft delete
PUT    /api/v1/documents/{id}/restore     # Restore soft-deleted
GET    /api/v1/documents/{id}/versions    # List version history

GET    /api/v1/transactions/{id}/documents # List documents for a transaction
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

#### Shared Active Transactions Workspace (`/api/v1/workspace`)

```
GET    /api/v1/workspace/ai-briefing        # Topbar AI briefing:
                                            #   critical_count, needs_attention_count,
                                            #   on_track_count, suggested_focus
GET    /api/v1/workspace/sidebar-kpis       # Sidebar KPI tiles:
                                            #   overdue_tasks, closing_this_week,
                                            #   active_deals, pipeline_value
GET    /api/v1/workspace/deal-state-counts  # Sidebar Deals counts:
                                            #   active_transactions, pending, closed, all_transactions
GET    /api/v1/workspace/transaction-cards  # Active transaction cards:
                                            #   client, address, status_pill, why_badges,
                                            #   ai_next_step, milestone_bar, info_badges,
                                            #   key_dates, grouped_contacts, price,
                                            #   Supports: ?view=personal|team,
                                            #   ?state_filter=active|pending|closed|all,
                                            #   ?tab=all|overdue|today|closing_soon|
                                            #        in_inspection|on_track|unhealthy,
                                            #   ?sort=urgency|close_date|client_name|price,
                                            #   ?search=, ?team_member_id=

# Key dates management (inline edit from expanded drawer)
PUT    /api/v1/transactions/{id}/key-dates  # Update one or more key milestone dates:
                                            #   em_delivered_date, inspection_response_date,
                                            #   appraisal_expected_date, cd_delivered_date,
                                            #   cleared_to_close_date, closing_date,
                                            #   closing_time, possession_date, possession_time

# Transaction history timeline
GET    /api/v1/transactions/{id}/history    # Searchable event timeline:
                                            #   events grouped by date (Today, Yesterday, etc.)
                                            #   Each: timestamp, description, detail, event_type
                                            #   Merges audit logs, communication logs, task
                                            #   completions, date changes, AI flags
                                            #   Supports: ?search= for filtering

# AI chat for workspace context
POST   /api/v1/workspace/ai-chat           # Contextual AI assistant:
                                            #   message, optional transaction_id context
                                            #   Returns: response, suggested_actions[]
                                            #   Quick-action prompts: "Show overdue tasks",
                                            #   "Draft inspection response", "Summarize deal"
```

**Notes:**
- `?view=personal` returns only the user's own deals (Agent View)
- `?view=team` returns all team deals with assignee info (Team Leader View)
- `?search=` searches across client names, vendor names, companies, dates, addresses
- `?sort=urgency` (default) sorts by overdue + soonest closing first
- `?tab=in_inspection` means the inspection response has not yet been sent
- `pipeline_value` sums purchase_price of currently active transactions
- Status pills and "why" badges are computed server-side from transaction
  state, task state, due dates, message counts, and missing-doc conditions
- Dashboard landing pages reuse these same aggregation services
- Key dates are returned as part of transaction card data and are editable
  inline via the `PUT /key-dates` endpoint; changes are audit-logged
- Transaction history merges multiple event sources into a unified timeline;
  the frontend displays it in the Transaction History panel

#### Role-Specific Dashboard Landing Pages (`/api/v1/dashboard`)

```
# --- Solo Agent Dashboard ---
GET    /api/v1/dashboard/agent/hero         # Hero card data:
                                            #   health_score (0-100), health_descriptor,
                                            #   action_queue (ranked transactions needing
                                            #   intervention today), drift_diagnostics
                                            #   (deals drifting + why), fast_filter_counts
GET    /api/v1/dashboard/agent/production   # Production snapshot:
                                            #   pending_gci, pending_volume, closings_ytd,
                                            #   closings_lifetime, active_transaction_count
GET    /api/v1/dashboard/agent/priority-cards  # Priority transaction cards:
                                            #   closing_soon, in_inspection, documents_needed,
                                            #   next_step_cta, key_tasks, key_dates,
                                            #   contacts, footer_actions
GET    /api/v1/dashboard/agent/intelligence # Side rail AI intelligence:
                                            #   portfolio_insights, missing_doc_concentration,
                                            #   recent_communication_highlights

# --- Team Leader Dashboard ---
GET    /api/v1/dashboard/team/intervention  # Team intervention queue:
                                            #   ranked by likelihood of breaking,
                                            #   closings_in_7d_with_dependency,
                                            #   no_client_touch_72h, missing_signatures,
                                            #   agents_needing_coaching
GET    /api/v1/dashboard/team/performance   # Team performance modules:
                                            #   agent_board (drill-down per agent),
                                            #   team_financials, pipeline_health,
                                            #   annual_pace, closings_next_14d
GET    /api/v1/dashboard/team/drift         # Drift / discipline metrics:
                                            #   unresolved_dependencies, stale_communication,
                                            #   document_gaps, coaching_opportunities
GET    /api/v1/dashboard/team/intelligence  # Team side rail:
                                            #   ai_portfolio_intel, coach_prompts,
                                            #   docs_blocking_milestones, recent_comms

# --- Attorney Dashboard ---
GET    /api/v1/dashboard/attorney/queue     # Attorney queue data:
                                            #   hard_stops_today, release_ready_packets,
                                            #   active_matters, reviewed_volume
GET    /api/v1/dashboard/attorney/hero      # Attorney hero card:
                                            #   legal_health_score, matters_needing_judgment,
                                            #   action_list (critical approval gates),
                                            #   drift_summary (blocked, missing_formal_docs,
                                            #   release_ready)
GET    /api/v1/dashboard/attorney/matter-cards  # Matter cards:
                                            #   matter_name, status_pills, review_queue,
                                            #   key_dates, ai_prepared_next_step,
                                            #   audit_trail, packet_actions
                                            #   Supports: ?tab=all|needs_review|missing_docs|
                                            #        ready_to_release|clean_files
GET    /api/v1/dashboard/attorney/state-rules   # State rules data:
                                            #   closing_mode, recording_timelines,
                                            #   disbursement_timing, same_day_release_checks

# --- FSBO Customer Workspace ---
GET    /api/v1/dashboard/fsbo/overview      # FSBO overview:
                                            #   critical_next_steps, days_to_close,
                                            #   share_links_live, missing_documents
GET    /api/v1/dashboard/fsbo/properties    # Property portfolio:
                                            #   property cards with status, closing_date,
                                            #   missing_docs, new_messages, fsbo_state
                                            #   (listing_prep | under_contract)
GET    /api/v1/dashboard/fsbo/documents     # FSBO document view:
                                            #   documents with status (missing, in_progress,
                                            #   uploaded, verified, complete),
                                            #   role-appropriate actions
GET    /api/v1/dashboard/fsbo/milestones    # Milestones & messages:
                                            #   milestone_timeline, messages, ai_guidance
GET    /api/v1/dashboard/fsbo/share-link    # Milestone sharing:
POST   /api/v1/dashboard/fsbo/share-link    #   create/manage expirable read-only links
```

#### Health & System

```
GET    /api/v1/health                      # Health check
GET    /api/v1/health/ready                # Readiness check (DB connectivity)
```

### 3.3 Permission Matrix (Phase 1)

| Endpoint | Admin | TeamLead | Agent | Elf | Attorney | Client | FSBO Customer | Vendor |
|----------|-------|----------|-------|-----|----------|--------|---------------|--------|
| User management | CRUD | Read team | Read self | Read self | Read self | Read self | Read self | Read self |
| Invite users | Yes | Team only | Own elves | No | No | No | No | No |
| Create transaction | Yes | Yes | Yes | No | No | No | No | No |
| View transactions | All | Team | Own/assigned | Assigned | Assigned (attorney matters) | Own | Own properties | Own |
| Manage tasks | All | Team templates | Own txn | Assigned txn | Attorney-owned tasks | No | No | No |
| Task templates | System-wide | Team-wide | Personal | No | No | No | No | No |
| Upload documents | Yes | Yes | Yes | Yes | Yes (legal packets) | Yes (no delete) | Yes (no delete) | Yes (own) |
| Delete documents | Yes | Yes | Yes | Yes | Yes (own uploads) | Flag only | Flag only | No |
| View documents | All | Team | Own txn | Assigned txn | Assigned txn | Own txn | Own property docs | Own uploads |
| Active Transactions workspace | All | Team + personal toggle | Own | Assigned | Attorney queue | No | No | No |
| Dashboard landing page | Admin dashboard | Team Leader dashboard | Solo Agent dashboard | Solo Agent dashboard | Attorney dashboard | Client portal | FSBO workspace | Vendor portal |
| Approve/release packets | No | No | No | No | Yes (attorney-owned) | No | No | No |
| AI-prepared legal work | No | No | No | No | Review only (no delegation) | No | No | No |
| Milestone sharing | No | No | No | No | No | Share own | Share own (expirable links) | No |
| Confidence settings | Global floor | Team threshold | No | No | No | No | No | No |
| Audit logs | Full | Team | No | No | Own matters | No | No | No |

---

## 4. Frontend UI/UX Design

### 4.1 Design System (Client-Approved Designs)

**Visual approach:** B2B institutional trust pack — dark sidebar + light content
surface + high-density transaction cards. Customer-facing portals (FSBO) use a
simplified but brand-consistent shell.

**Approved HTML design references (2026-03-26):**
- `completed_designs/ve-active_transactions.html` — shared Active Transactions workspace
- `completed_designs/ve-homepage_dashboard-solo_agent.html` — Solo Agent dashboard landing
- `completed_designs/ve-homepage_dashboard-team_leader.html` — Team Leader dashboard landing
- `completed_designs/ve-fsbo_dashboard.html` — FSBO Customer workspace
- `completed_designs/ve-attorney_dashboard.html` — Attorney dashboard landing

**Additional brand references:** `data/ve-brandkit.txt` and `data/ve-style-sheet.txt`

- **Colors — brand-aligned semantic token system (CSS variables, white-label propagation):**
  ```css
  /* Brand */
  --brand-navy: #1b2b3c;           /* primary trust surfaces, nav, headers */
  --brand-orange: #ee7623;         /* CTAs, key highlights, active states */
  --brand-orange-dark: #c85f13;    /* CTA hover / pressed */
  --brand-bg: #f5f7fa;             /* default page background */
  --brand-ai-glow: #ffeec2;        /* subtle AI surfaces only */
  --text-primary: #333333;         /* max-contrast slate */

  /* Functional states */
  --status-critical: #c8322f;      --status-critical-bg: #fff0f0;
  --status-warning: #c07a0a;       --status-warning-bg: #fffbf0;
  --status-success: #1a7a52;       --status-success-bg: #edf7f3;
  --status-info: #2c4c7f;          --status-info-bg: #eef3fc;
  --status-neutral: #7a7a7a;       --status-neutral-bg: #f0f0ee;

  /* Surfaces */
  --surface-card: #ffffff;
  --surface-sidebar: #1e3356;
  --surface-sidebar-hover: #284168;
  --surface-border: #e2e2e0;
  --surface-border-strong: #cacac8;
  ```
  Status pills use tint + border + text for readability, while card edge bars,
  briefing badges, and inline urgency states carry stronger emphasis.
- **Typography:** IBM Plex Sans across the application workspace; IBM Plex Mono
  for numbers, dates, countdowns, phone numbers, file IDs, and badge counts.
  Limited Lora serif accents may be used for approved brand/display headings
  (hero card titles, dashboard section headers) per the design files; body/UI
  copy remains IBM Plex Sans. Do not introduce role-specific alternates such as
  DM Sans.
- **Numeric handling:** apply `font-variant-numeric: tabular-nums lining-nums`
  anywhere the UI displays money, dates, percentages, phone numbers,
  commissions, file IDs, or deadlines.
- **Layout:** Dark sidebar + slim topbar + page header + scrollable transaction
  area.
- **Interaction rules:** 6px corner radius for professional components and a
  minimum 48x48px target size for interactive elements.
- **Components:** shadcn/ui + custom workspace components matching the approved
  Active Transactions patterns.
- **Responsive:** Desktop-first with mobile breakpoints; preserve scan density
  without collapsing the workspace into a consumer-style layout.

### 4.2 Page Structure

**Scope update (2026-03-26):** Dashboard landing pages are now approved for
Solo Agent, Team Leader, Attorney, and FSBO. The Active Transactions workspace
remains the shared MVP transaction view for all internal roles. The page tree
below reflects the full approved scope.

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
|-- Main App (protected — internal roles)
|   |-- Topbar (shared shell)
|   |   |-- Brand lockup + AI indicator
|   |   |-- Today's AI Briefing chip (Critical / Needs Attention / On Track)
|   |   |-- Global search
|   |   |-- Notifications bell
|   |   |-- User chip
|   |   `-- Contextual CTA (e.g., + New Transaction)
|   |
|   |-- Sidebar (shared shell — KPIs and nav vary by role)
|   |   |-- KPI tiles (2x2 grid, role-specific metrics)
|   |   |-- Dashboard link
|   |   |-- Deals
|   |   |   |-- Active Transactions
|   |   |   |-- Pending
|   |   |   |-- Closed
|   |   |   `-- All Transactions
|   |   |-- Workflow
|   |   |   |-- My Task Queue
|   |   |   |-- All Documents
|   |   |   `-- Closing Calendar
|   |   |-- Intelligence
|   |   |   |-- AI Suggestions
|   |   |   |-- Analytics
|   |   |   `-- Settings
|   |   |-- Team (Team Lead only)
|   |   |   |-- Agents
|   |   |   `-- Task Templates
|   |   |-- Pinned CTA (+ New Transaction)
|   |   `-- User profile card
|   |
|   |-- Dashboard Landing Pages (role-specific, approved designs)
|   |   |-- Solo Agent Dashboard
|   |   |   |-- Upload intake card (drag/drop to start transaction)
|   |   |   |-- Hero card (health score, action queue, drift diagnostics)
|   |   |   |-- Production snapshot (GCI, volume, closings)
|   |   |   |-- Priority transaction cards
|   |   |   `-- Side rail (AI intelligence, missing docs, comms)
|   |   |-- Team Leader Dashboard
|   |   |   |-- Upload intake card
|   |   |   |-- Hero card (team health score, intervention queue)
|   |   |   |-- Drift / discipline metrics
|   |   |   |-- Agent board with drill-down
|   |   |   |-- Team financials and pipeline
|   |   |   `-- Side rail (AI intel, coach prompts, docs blocking)
|   |   `-- Attorney Dashboard
|   |       |-- Upload intake card (legal packets)
|   |       |-- Hero card (legal health score, approval gates)
|   |       |-- Filter tabs (All, Needs Review, Missing Docs, Ready To Release, Clean Files)
|   |       |-- Matter cards (review queue, key dates, AI next step)
|   |       `-- State rules modal / recording calendar
|   |
|   |-- Active Transactions Workspace (shared MVP for Agent, Elf, Team Lead, Attorney)
|   |   |-- Agent/Elf personal view
|   |   |-- Team Lead team/personal toggle
|   |   `-- Attorney queue view (filtered by attorney matters)
|   |
|   |-- Transaction Detail
|   |   |-- Overview
|   |   |-- Tasks
|   |   |-- Documents
|   |   |-- Parties
|   |   `-- Communications
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
|-- FSBO Customer Workspace (protected — customer-facing)
|   |-- Sidebar
|   |   |-- KPI tiles (critical next steps, days to close, share links, missing docs)
|   |   |-- Dashboard
|   |   |-- My Properties
|   |   |-- Documents
|   |   |-- Milestones & Messages
|   |   |-- Ask Velvet Elves AI
|   |   |-- Notifications
|   |   `-- Sharing
|   |-- Portal tabs: Overview | Properties | Documents | Support
|   |-- Property portfolio cards (listing-prep and under-contract states)
|   |-- Plain-English AI guidance panel
|   |-- Milestone sharing (expirable read-only links)
|   `-- Support/guide contact area
|
`-- Client Portal (protected — simplified)
    |-- My Transactions
    |-- Documents
    |-- Milestones
    `-- Agent Info
```

### 4.3 Key UI Components (Phase 1)

#### 4.3.1 Agent/Elf Active Transactions Workspace (Client-Approved Redesign)

**Reference:** `completed_designs/ve-active_transactions.html`
**Scope note:** This section supersedes the earlier dashboard-first planning.
The approved detailed screen is the Active Transactions workspace; dashboard
landing pages are now also approved (see 4.3.1c–4.3.1f).

```text
+--------------------------------------------------------------------------+
| SIDEBAR                                                                  |
| - KPI tiles: Overdue Tasks, Closing This Week, Active Deals, Pipeline    |
| - Deal states: Active Transactions, Pending, Closed, All Transactions    |
| - Workflow: Task Queue, Closing Calendar, All Documents                  |
| - Intelligence: AI Suggestions, Analytics                                |
| - Footer CTA: New Transaction                                            |
+--------------------------------------------------------------------------+
| TOPBAR                                                                   |
| - Greeting + global search                                               |
| - Today's AI Briefing chip with Critical / Needs Attention / On Track    |
| - Notification access + profile                                          |
+--------------------------------------------------------------------------+
| PAGE HEADER                                                              |
| - Title: Active Transactions                                             |
| - Search + sort                                                          |
| - Tabs: All | Overdue | Due Today | Closing Soon | In Inspection |       |
|         On Track | Unhealthy                                             |
+--------------------------------------------------------------------------+
| TRANSACTION CARD STACK                                                   |
| - Header: urgency edge, status pill, address/client summary, why badges  |
| - Inline AI next step banner                                             |
| - Milestone bar: Contract, EM, Inspection, Appraisal, CD, CTC, Close     |
| - Info badges: tasks, unread email, notes, docs, contact touchpoints     |
| - Expandable drawer: Tasks | Key Dates | Contacts                        |
| - Footer actions: Add Task, Upload, View Documents, Print Checklist      |
+--------------------------------------------------------------------------+
| SUPPORTING OVERLAYS                                                      |
| - Add Task modal (name, method, due date, assign to, AI suggestions)     |
| - New Transaction quick-create modal (AI Import + manual fields)         |
| - Transaction Documents modal                                            |
| - All Documents AI Search modal                                          |
| - Add Contact inline modal (company, name, phone, email)                 |
| - Transaction History panel (searchable event timeline)                  |
| - Edit Date popover (inline key-date changes)                            |
| - Floating AI Chat panel (contextual assistant)                          |
| - Global drag-and-drop document intake prompt                            |
+--------------------------------------------------------------------------+
```

**Key design patterns:**
- **Topbar AI briefing**: "Today's AI Briefing" chip with Critical / Needs
  Attention / On Track counts, always available as a filter shortcut.
- **Sidebar KPI tiles**: overdue tasks, closing this week, active deals, and
  pipeline value presented as actions, not just passive metrics.
- **Deals / Workflow / Intelligence nav grouping**: the page separates state
  filters from workflow shortcuts and AI/analytics shortcuts.
- **Page-level transaction tabs**: All, Overdue, Due Today, Closing Soon,
  In Inspection, On Track, Unhealthy.
- **Transaction cards**: left-edge urgency indicator + status pill + "why"
  badges so the user can understand risk without opening the card.
- **AI next-step banner**: inline contextual action area at the top of the card
  that explains what should happen next and why it matters.
- **Milestone bar**: compact horizontal deal-progress view for Contract, EM,
  Inspection, Appraisal, CD Delivered, CTC, and Close.
- **Info badges**: tasks, unread emails, notes, missing docs, client touch,
  lender touch, and history are surfaced before expansion.
- **Expanded 3-column drawer**: Tasks, Key Dates, Contacts, followed by an AI
  suggestions strip and footer actions.
- **Key Dates column**: lists EM Delivered, Inspection Response, Appraisal
  Expected, CD Delivered, Cleared to Close, Closing Date (with time), and
  Possession (with time); each date has a pencil-edit icon that opens an
  inline Save/Cancel popover; overdue dates shown in red.
- **Grouped contact cards**: buyer, listing agent, lender, title, etc. each
  support expand/collapse, one-click call/email, and add-secondary-contact
  flows; empty slots show "Add [role]" links.
- **Add Task modal**: task name, completion method (Phone Call, Email,
  DocuSign/E-Signature, In Person, Upload Document, Online Portal, AI Agent,
  Other), due date, assign-to (self, AI Agent, team members), and "Get AI
  Suggestions" button with expandable AI Suggested Approaches.
- **New Transaction quick-create modal**: AI Import action ("Paste a contract
  or MLS listing — AI will auto-fill all fields"); manual fields: Client Name,
  Property Address, City/ZIP, Transaction Type, Purchase Price, Contract Date,
  Projected Closing Date, Lender/Title Company, Notes; "Create with AI
  Checklist" action.
- **Add Contact modal**: Company Name, First Name, Last Name, Phone Number,
  Email Address.
- **Transaction History panel**: searchable event timeline organized by date
  headings (Today, Yesterday, etc.) merging AI flags, emails, task
  completions, date confirmations, and offer events.
- **Floating AI Chat panel**: "Velvet Elves AI" contextual assistant with
  deal-specific quick-action prompts.
- **Integrated overlays**: Transaction Documents modal, All Documents AI
  Search modal, and Edit Date popover are all part of the primary workspace.
- **Checklist print action**: each transaction drawer exposes a print action
  fed from user/team checklist templates.

#### 4.3.1b Team Lead Active Transactions Workspace

```text
Team Lead Active Transactions Workspace

- Shared shell:
  - Same topbar, sidebar, tabs, transaction-card system, and overlays as Agent/Elf view
  - Toggle allows Team Lead to switch between personal and team scopes

- Team view adjustments:
  - KPI tiles and AI briefing aggregate across the full team
  - Transaction cards include assignee name and optional assignee filter
  - Activity summaries, unhealthy counts, and upcoming closings are team-scoped
  - Team task-template actions and oversight shortcuts are available

- Personal view adjustments:
  - Uses the same Active Transactions workspace but scoped to the Team Lead's own deals
```

**Why toggle:** Most Team Leads also sell real estate and need both a personal
Active Transactions view (their own deals) and a team oversight view (all team
deals).

#### 4.3.1c Solo Agent Dashboard Landing Page

**Reference:** `completed_designs/ve-homepage_dashboard-solo_agent.html`

```text
+--------------------------------------------------------------------------+
| SIDEBAR (same shared shell as Active Transactions)                       |
| - KPI tiles: Overdue Tasks, Closing This Week, Active Deals, Pipeline   |
| - Dashboard (active), Deals, Workflow, Intelligence                     |
+--------------------------------------------------------------------------+
| TOPBAR                                                                   |
| - Brand lockup + AI indicator                                           |
| - Today's AI Briefing chip (Critical / Needs Attention / On Track)      |
| - Search, notifications, user chip, + New Transaction CTA               |
+--------------------------------------------------------------------------+
| UPLOAD INTAKE CARD                                                       |
| - Prominent drag/drop or browse zone for document-first intake          |
| - AI reads docs, builds transaction shell, suggests milestones,         |
|   identifies missing docs, routes to Active Transactions                |
| - "Open intake" outline button                                          |
+--------------------------------------------------------------------------+
| COMMAND GRID (3-column responsive layout)                                |
| - Hero card (1.55fr):                                                   |
|   - Serif heading, health score ring (conic gradient, 0-100)            |
|   - "Why deals are drifting" diagnostics                                |
|   - Action queue: ranked transactions needing intervention today        |
|   - Fast filter buttons: critical closings, missing responses,          |
|     stale communication, document blockers                              |
| - Production snapshot (.95fr):                                          |
|   - Pending GCI, pending volume, closings YTD/lifetime,                 |
|     active transaction counts                                           |
| - Transaction overview (.8fr):                                          |
|   - Priority cards: closing soon, in inspection, documents needed       |
|   - Next-step CTA, key tasks, key dates, contacts, footer actions      |
+--------------------------------------------------------------------------+
| SIDE RAIL                                                                |
| - AI portfolio intelligence                                             |
| - Missing-doc concentration                                             |
| - Recent communication highlights                                       |
+--------------------------------------------------------------------------+
```

**Key design patterns (dashboard-specific):**
- **Upload intake card**: document-first engagement at the top of the dashboard;
  AI handles classification, transaction creation, and routing.
- **Command grid**: 3-column responsive layout mixing a hero card with metric
  and overview cards. Columns use fractional widths (1.55fr / .95fr / .8fr).
- **Health score ring**: conic-gradient progress indicator (0-100) with
  descriptive text summarizing portfolio health.
- **Drift summary rows**: quantified workflow state with color-coded emphasis
  (e.g., "2 deals need inspection docs").
- **Action queue**: prioritized list of transactions needing intervention today
  with status dots and inline quick-action buttons.
- **Fast filter buttons**: one-click filters that open curated views in the
  Active Transactions workspace.
- **Dashboard cards, fast filters, and AI prompts deep-link into the shared
  Active Transactions workspace** — they do not create isolated dead-end pages.

#### 4.3.1d Team Leader Dashboard Landing Page

**Reference:** `completed_designs/ve-homepage_dashboard-team_leader.html`

```text
+--------------------------------------------------------------------------+
| SIDEBAR                                                                  |
| - KPI tiles: Deals At Risk, Closing in 14 Days, Active Deals, Pipeline  |
| - Dashboard (active), Deals, Workflow, Team (Agents, Task Templates),    |
|   Intelligence (includes AI Coach link — future paid feature, not MVP)   |
+--------------------------------------------------------------------------+
| TOPBAR (same shared shell)                                               |
+--------------------------------------------------------------------------+
| UPLOAD INTAKE CARD (same as Solo Agent)                                  |
+--------------------------------------------------------------------------+
| COMMAND GRID (3-column, same layout system)                              |
| - Hero card:                                                            |
|   - Team health score ring                                              |
|   - Intervention queue ranked by likelihood of breaking                 |
|   - Drift metrics: closings in 7d with unresolved dependency,           |
|     no client touch in 72+ hrs, missing signatures, agent coaching      |
|   - Filter buttons: needs judgment, stale deals, doc gaps, coaching     |
| - Team performance modules:                                             |
|   - Agent board with drill-down per agent                               |
|   - Team financials, pipeline health, annual pace                       |
|   - Closings in the next 14 days                                       |
| - Side rail:                                                            |
|   - AI portfolio intelligence, coach prompts                            |
|   - Documents blocking milestones, recent communication                 |
+--------------------------------------------------------------------------+
```

**Key differences from Solo Agent:**
- **Sidebar Team section**: additional navigation group with Agents and Task
  Templates links.
- **KPIs are team-aggregated**: "Deals at Risk" replaces "Overdue Tasks";
  larger numbers reflect the full team pool.
- **AI Coach link**: shown in Intelligence section but is a future paid feature
  ($79/agent/month). MVP may preserve architecture hooks or feature-flagged
  placeholders but should not scope active implementation.
- **Intervention queue**: ranked by breaking likelihood rather than personal
  urgency; includes coaching opportunities.

#### 4.3.1e Attorney Dashboard Landing Page

**Reference:** `completed_designs/ve-attorney_dashboard.html`

```text
+--------------------------------------------------------------------------+
| SIDEBAR                                                                  |
| - KPI tiles: Hard Stops Today, Release-Ready Packets, Active Matters,   |
|   Reviewed Volume                                                       |
| - Deals: Attorney Queue, Pending Review, Ready To Release, Clean Files  |
| - Workflow: Missing Documents, Recording Calendar, Communication Log    |
| - Intelligence: AI Suggestions, State Rules, Settings                   |
+--------------------------------------------------------------------------+
| TOPBAR (same shared shell — "Attorney Workspace" subtitle)              |
+--------------------------------------------------------------------------+
| UPLOAD INTAKE CARD (legal packets)                                       |
| - Accepts: title commitments, settlement statements, affidavits,        |
|   signed amendments, recording packets                                  |
| - AI extracts deadlines, compares versions, indexes exhibits,           |
|   flags missing formal docs, routes legal judgment to attorney queue    |
| - CTAs: "Open intake" and "Open release queue"                          |
+--------------------------------------------------------------------------+
| COMMAND GRID                                                             |
| - Hero card:                                                            |
|   - Legal health score (0-100) focused on approval gates                |
|   - "N matters need legal judgment before closing stays on track"       |
|   - Action list: critical approval gates                                |
|   - Drift summary: blocked matters, missing formal docs,               |
|     release-ready packets                                               |
|   - Filter buttons: needs attorney judgment, missing notarized docs,    |
|     ready to release after sign-off, recording/disbursement timing      |
+--------------------------------------------------------------------------+
| FILTER TABS                                                              |
| - All | Needs Review | Missing Docs | Ready To Release | Clean Files    |
+--------------------------------------------------------------------------+
| MATTER CARD STACK                                                        |
| - Header: matter name, status pills (Critical, Today, Missing doc)      |
| - Expandable drawer (3-column):                                         |
|   - Review queue: tasks with attorney sign-off checkboxes               |
|   - Key dates: deadlines with status color coding                       |
|   - Next step: AI-prepared action with context                          |
| - Footer: View docs, Audit trail, Send packet, price                    |
+--------------------------------------------------------------------------+
| STATE RULES MODAL                                                        |
| - Closing mode, recording timelines, disbursement timing,               |
|   same-day release checks                                               |
| - Recording calendar and legal/audit quick actions                      |
+--------------------------------------------------------------------------+
```

**Key design patterns (attorney-specific):**
- **Attorney-specific KPIs**: "Hard Stops Today" and "Release-Ready Packets"
  replace generic task/deal metrics.
- **Legal health score**: operational health focused on sign-off gates and
  release timing, not general portfolio health.
- **Matter cards**: similar structure to transaction cards but oriented around
  legal review queue, sign-off gates, and packet release actions.
- **Explicit AI-vs-human boundary**: the dashboard makes the line between
  AI-prepared work and human legal judgment explicit. Final legal position,
  packet release approval, and same-day disbursement exceptions remain
  human-owned.
- **Release queue**: separate action path for pre-closing packet staging and
  attorney-specific approval gates.
- **State rules surface**: modal/watch for closing mode, recording timelines,
  disbursement timing, and same-day release checks.

#### 4.3.1f FSBO Customer Workspace

**Reference:** `completed_designs/ve-fsbo_dashboard.html`

```text
+--------------------------------------------------------------------------+
| SIDEBAR (simplified, customer-facing)                                    |
| - KPI tiles: Critical Next Steps, Days to Close, Share Links Live,      |
|   Missing Documents                                                     |
| - Dashboard, My Properties, Documents, Milestones & Messages            |
| - Ask Velvet Elves AI, Notifications, Sharing                           |
+--------------------------------------------------------------------------+
| TOPBAR ("FSBO WORKSPACE" subtitle)                                       |
| - Brand lockup, AI briefing chip, search, notifications, user chip      |
| - "Share milestones" primary CTA                                        |
+--------------------------------------------------------------------------+
| PORTAL TABS                                                              |
| - Overview | Properties | Documents | Support (with count badges)        |
+--------------------------------------------------------------------------+
| PROPERTY PORTFOLIO STRIP                                                 |
| - Portfolio cards per property:                                          |
|   - Property title (serif heading)                                      |
|   - Status pill (e.g., "Needs response")                                |
|   - Portfolio chips: closing date, missing docs, new messages            |
|   - Quick actions: Open timeline, Share link                            |
| - Supports both listing-prep and under-contract views                   |
+--------------------------------------------------------------------------+
| PLAIN-ENGLISH AI GUIDANCE                                                |
| - Next decision, why it matters, upcoming milestones,                   |
|   current document blockers in plain English                            |
| - Glossary-style explanations                                           |
| - Boundary notice: VE coordinates workflow but does not act as the      |
|   customer's agent or provide legal advice                              |
+--------------------------------------------------------------------------+
| MILESTONE SHARING                                                        |
| - Read-only milestone links with expiry and viewer-open notifications   |
| - Shared viewers see timeline and key dates only — no internal workflow  |
|   details, task editing, document deletion, or internal notes           |
+--------------------------------------------------------------------------+
| SUPPORT / GUIDE CONTACT AREA                                             |
| - Assigned Velvet Elves support/guide contacts                          |
+--------------------------------------------------------------------------+
```

**Key design patterns (FSBO-specific):**
- **Portal tabs** (not filter tabs): navigate between content sections
  (Overview, Properties, Documents, Support).
- **Portfolio cards**: property-centric alternative to transaction cards;
  oriented toward property ownership rather than deal management.
- **Property-centric KPIs**: "Days to Close", "Missing Documents", and "Share
  Links Live" replace deal-management metrics.
- **Plain-English AI guidance**: customer-facing AI that explains next steps,
  deadlines, and document requirements without internal jargon.
- **Milestone sharing**: expirable read-only links; shared viewers see progress
  and key dates but cannot edit tasks, delete documents, or view internal
  workflow notes.
- **Minimal workflow exposure**: FSBO customers see document status states
  (Missing, In Progress, Uploaded, Verified, Complete) and milestone progress
  but not internal task management, approval workflows, or back-office notes.
- **Document status states**: customer-facing documents surface states like
  Missing, In Progress, Uploaded, Verified, or Complete with role-appropriate
  actions (Upload New Version, Flag Issue).

#### 4.3.2 Transaction Detail — Tabbed View

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

#### 4.3.3 Admin — Task Template Manager

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

  // Main app — role-specific dashboard landing pages (approved 2026-03-26)
  DASHBOARD: '/dashboard',                          // auto-routes by role
  DASHBOARD_AGENT: '/dashboard/agent',              // NEW: Solo Agent dashboard
  DASHBOARD_TEAM_LEADER: '/dashboard/team',         // NEW: Team Leader dashboard
  DASHBOARD_ATTORNEY: '/dashboard/attorney',        // NEW: Attorney dashboard
  DASHBOARD_ADMIN: '/dashboard/admin',              // existing admin dashboard
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

  // Workflow section
  TASK_QUEUE: '/tasks/queue',
  CLOSING_CALENDAR: '/closing-calendar',
  DOCUMENTS: '/documents',
  ALL_DOCUMENTS: '/documents/all',

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

  // Attorney workspace
  ATTORNEY_QUEUE: '/attorney/queue',                // NEW: attorney matter queue
  ATTORNEY_RELEASE_QUEUE: '/attorney/releases',     // NEW: release-ready packets
  ATTORNEY_STATE_RULES: '/attorney/state-rules',    // NEW: state rules modal/view
  ATTORNEY_RECORDING_CALENDAR: '/attorney/recording-calendar', // NEW

  // FSBO Customer workspace
  FSBO_DASHBOARD: '/fsbo',                          // NEW: FSBO overview
  FSBO_PROPERTIES: '/fsbo/properties',              // NEW: property portfolio
  FSBO_PROPERTY_DETAIL: '/fsbo/properties/:id',     // NEW
  FSBO_DOCUMENTS: '/fsbo/documents',                // NEW: document submission
  FSBO_MILESTONES: '/fsbo/milestones',              // NEW: milestones & messages
  FSBO_SHARE: '/fsbo/share',                        // NEW: milestone sharing
  FSBO_AI_HELP: '/fsbo/ask-ai',                     // NEW: plain-English AI guidance

  // Admin
  ADMIN_USERS: '/admin/users',              // NEW
  ADMIN_USER_DETAIL: '/admin/users/:userId',
  ADMIN_TEMPLATES: '/admin/task-templates',  // NEW
  ADMIN_TEMPLATE_DETAIL: '/admin/task-templates/:id', // NEW
  ADMIN_TEMPLATE_IMPORT: '/admin/task-templates/import', // NEW
  ADMIN_CONFIDENCE: '/admin/confidence',     // NEW
  ADMIN_AUDIT_LOGS: '/admin/audit-logs',     // NEW
  ADMIN_TENANT: '/admin/tenant',             // NEW

  // Shared milestone viewer (public, read-only)
  MILESTONE_VIEWER: '/milestones/:shareToken',      // NEW: expirable public link
} as const;
```

### 4.5 Frontend State Architecture

```text
React Query (TanStack Query)
|-- Server State (cached via React Query)
|   |-- /auth/me                      -> current user
|   |-- /workspace/ai-briefing        -> topbar AI briefing counts
|   |-- /workspace/sidebar-kpis       -> sidebar KPI tiles
|   |-- /workspace/deal-state-counts  -> Active/Pending/Closed/All counts
|   |-- /workspace/transaction-cards  -> collapsible card data
|   |-- /dashboard/agent/*            -> Solo Agent dashboard data (hero, production, priority, intel)
|   |-- /dashboard/team/*             -> Team Leader dashboard data (intervention, performance, drift)
|   |-- /dashboard/attorney/*         -> Attorney dashboard data (queue, hero, matters, state-rules)
|   |-- /dashboard/fsbo/*             -> FSBO workspace data (overview, properties, docs, milestones)
|   |-- /transactions                 -> transaction list
|   |-- /tasks                        -> task list
|   |-- /contacts                     -> contact directory
|   |-- /documents                    -> transaction documents
|   |-- /documents/search             -> all-documents AI search
|   |-- /task-templates               -> template library
|   `-- /audit-logs                   -> audit trail
|
|-- Client State (React Context)
|   |-- AuthContext                   -> JWT token, user session, current role
|   |-- ThemeContext                  -> white-label branding
|   |-- WorkspaceViewContext          -> Team Lead personal/team toggle
|   |-- WorkspaceFilterContext        -> deal-state + page-tab filters
|   |-- DashboardContext              -> role-specific dashboard state, command grid layout
|   |-- GlobalDropzoneContext         -> workspace-wide document drop handling
|   `-- NotificationContext           -> toast/alert state
|
`-- Form State (React Hook Form)
    |-- TransactionForm
    |-- TaskTemplateForm
    |-- ContactForm
    |-- UserInviteForm
    |-- FSBOShareForm                 -> milestone sharing with expiry
    `-- AttorneyReleaseForm           -> packet release approval
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
   - Update `users` table (new columns)
   - Update `transactions` table (expanded fields)
   - Add `transaction_assignments` table
   - Add `transaction_parties` table
   - Add `task_templates` table
   - Update `tasks` table (new columns)
   - Update `documents` table (version control, classification)
   - Add `communication_logs` table
   - Add `audit_logs` table
   - Add `invitation_tokens` table
   - Add `confidence_settings` table
   - Create RLS policies
   - Create updated_at triggers

2. Update domain models:
   - `app/models/tenant.py` (new)
   - `app/models/team.py` (new)
   - `app/models/contact.py` (new)
   - `app/models/task_template.py` (new)
   - `app/models/transaction_party.py` (new)
   - `app/models/communication_log.py` (new)
   - `app/models/audit_log.py` (new)
   - `app/models/invitation.py` (new)
   - Update `app/models/enums.py` (new enums)
   - Update `app/models/user.py` (new fields)
   - Update `app/models/transaction.py` (expanded fields)
   - Update `app/models/task.py` (new fields)
   - Update `app/models/document.py` (version control, etc.)

3. Update Pydantic schemas:
   - New schema files for each new model
   - Update existing schemas for expanded fields

**Frontend tasks:**
1. No major frontend changes in Week 1
2. Update route constants for new pages (including dashboard landing routes,
   attorney workspace routes, FSBO workspace routes, milestone viewer)
3. Plan component structure for all 5 approved designs:
   - Shared app shell (topbar + sidebar + content area)
   - Solo Agent dashboard (command grid + hero card + upload intake)
   - Team Leader dashboard (team metrics + intervention queue)
   - Attorney dashboard (matter cards + release queue + state rules)
   - FSBO workspace (portal tabs + portfolio cards + milestone sharing)
   - Shared Active Transactions workspace (existing)

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
   - `app/repositories/task_template_repository.py`
   - `app/repositories/transaction_party_repository.py`
   - `app/repositories/transaction_assignment_repository.py`
   - `app/repositories/communication_log_repository.py`
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
   - Configure buckets: `documents`, `avatars`, `logos`
   - Set bucket policies for access control

### 5.3 Milestone 1.3 — Authentication & User Management Backend (Week 3)

**Deliverables:**

- [ ] Supabase Auth integration (already partially done)
- [ ] Registration, login, password reset APIs (already partially done)
- [ ] Invite-based onboarding flow
- [ ] RBAC system with 6 roles (already partially done)
- [ ] Permission middleware (already partially done)
- [ ] Contact management API
- [ ] Vendor contact card API
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

3. Contact management:
   - `app/services/contact_service.py`
   - `app/api/v1/contacts.py`
   - CRUD with PII encryption
   - Search functionality
   - Vendor card feature (generate shareable link)

4. Confidence settings:
   - `app/services/confidence_service.py`
   - `app/api/v1/confidence.py`
   - Admin sets global floor
   - Team Lead sets team thresholds (validated >= admin floor)

5. Audit logging service:
   - `app/services/audit_service.py`
   - Middleware or decorator for automatic audit logging
   - Before/after state capture

6. Tests:
   - Auth flow tests (expand existing)
   - Invitation flow tests
   - RBAC permission tests (expand existing)
   - Contact CRUD tests
   - Confidence settings tests

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
- `transactions`: minimal fields → needs full expansion (including closing_mode, is_fsbo, fsbo_state)
- `tasks`: basic fields → needs template_id, target, AI fields
- `documents`: basic fields → needs versioning, classification, signature tracking
- `users.role`: enum expansion to include Attorney and FSBO_Customer
- `integrations`: adequate for Phase 1
- Missing: tenants, teams, contacts, task_templates, transaction_assignments, transaction_parties, communication_logs, audit_logs, invitation_tokens, confidence_settings

Migration strategy:
1. New migration adds all new tables with `IF NOT EXISTS`
2. `ALTER TABLE` adds new columns to existing tables with defaults
3. Existing data is preserved — no destructive changes
4. Run CSV import after migration to populate `task_templates`
5. Apply RLS policies after data migration

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
- **More granular roles** (8 roles including Attorney and FSBO Customer vs ListedKit's simpler model)
- **Role-specific dashboard landing pages** (Solo Agent, Team Leader, Attorney, FSBO)
- **AI email automation** with safeguards (ListedKit has basic drafting)
- **Vendor communication system** with structured responses
- **White-label multi-tenancy** (ListedKit is single-brand)
- **Advertising module** for monetization
- **Task dependency engine** (more sophisticated than ListedKit's checklists)
- **Attorney workflow** with legal packet review, release gates, state-rule compliance
- **FSBO customer workspace** with property-centric views and plain-English AI guidance
- **Health score dashboards** with command-grid layout and drift diagnostics
