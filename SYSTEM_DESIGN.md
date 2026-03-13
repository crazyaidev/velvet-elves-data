# Velvet Elves - System Design Document

**Date:** 2026-03-05
**Scope:** Phase 1 (Milestones 1.1, 1.2, 1.3) — scalable for all future phases
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
  └── Users (Agent, Elf, TeamLead, Admin, Client, Vendor)
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
  role                   TEXT NOT NULL DEFAULT 'Agent',
  is_active              BOOLEAN NOT NULL DEFAULT TRUE,
  onboarding_completed   BOOLEAN NOT NULL DEFAULT FALSE,
  company_name           TEXT,
  company_logo_url       TEXT,
  bio                    TEXT,                        -- NEW: agent bio for client portal
  avatar_url             TEXT,                        -- NEW: profile photo
  notification_prefs     JSONB DEFAULT '{}'::jsonb,   -- NEW: notification on/off settings
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

  -- Key dates
  contract_acceptance_date DATE,
  closing_date             DATE,
  possession_date          DATE,

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
- `metadata_json` for extensibility without schema changes

#### 2.2.6 `transaction_assignments` — Who works on a transaction (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.transaction_assignments (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id  UUID NOT NULL REFERENCES public.transactions(id) ON DELETE CASCADE,
  user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  role_in_transaction TEXT NOT NULL,               -- 'primary_agent','elf','team_lead'
  assigned_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  assigned_by     UUID REFERENCES public.users(id),
  is_active       BOOLEAN DEFAULT TRUE,
  UNIQUE (transaction_id, user_id, role_in_transaction)
);

CREATE INDEX idx_tx_assign_transaction ON public.transaction_assignments (transaction_id);
CREATE INDEX idx_tx_assign_user ON public.transaction_assignments (user_id);
```

**Why:** Requirement 2.3 — transactions can be assigned to elf or agent, support reassignment and multiple participants.

#### 2.2.7 `transaction_parties` — External parties on a deal (NEW)

```sql
CREATE TABLE IF NOT EXISTS public.transaction_parties (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id  UUID NOT NULL REFERENCES public.transactions(id) ON DELETE CASCADE,
  contact_id      UUID REFERENCES public.contacts(id),       -- link to contacts directory
  party_role      TEXT NOT NULL,                               -- 'buyer','seller','listing_agent',
                                                               -- 'buyers_agent','loan_officer',
                                                               -- 'title_rep','title_company',
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
  channel           TEXT NOT NULL,                     -- 'email','system','ai_draft','note','document_action'
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
    ADMIN = "Admin"
    CLIENT = "Client"
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
    BUYER = "buyer"
    SELLER = "seller"
    INSPECTOR = "inspector"
    APPRAISER = "appraiser"
    HOME_WARRANTY = "home_warranty"
    OTHER = "other"

class CommunicationChannel(str, enum.Enum):
    EMAIL = "email"
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

GET    /api/v1/transactions/{id}/tasks    # List tasks for a transaction
POST   /api/v1/transactions/{id}/tasks/generate  # Generate tasks from use case + wizard data
```

#### Documents (`/api/v1/documents`)

```
POST   /api/v1/documents/upload           # Upload document(s)
GET    /api/v1/documents                  # List documents (with filters)
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

#### Dashboard Aggregation (`/api/v1/dashboard`) — NEW per redesign

```
GET    /api/v1/dashboard/triage             # Sidebar triage counts:
                                            #   overdue, due_tomorrow, active_deals, closing_soon
GET    /api/v1/dashboard/status-ribbon      # Header ribbon: overdue_tasks, due_tomorrow,
                                            #   closing_this_month, unread_messages
GET    /api/v1/dashboard/pipeline-summary   # Pipeline strip: closing_count, inspection_count,
                                            #   active_count, pending_count, total_pipeline_value,
                                            #   contextual subtitles per card
GET    /api/v1/dashboard/upcoming-closings  # Right column: closing countdown list
                                            #   (days_remaining, urgency_tier, client, address, date)
GET    /api/v1/dashboard/needs-attention    # Right column: cross-deal tasks needing attention
                                            #   (task, deal_name, deal_id, due_date, overdue flag)
GET    /api/v1/dashboard/transaction-cards  # Collapsible card data: client, address, stage_pill,
                                            #   milestone_timeline, next_deadline, badges,
                                            #   inline_tasks, key_dates, contacts
                                            #   Supports: ?view=personal|team, ?filter=, ?sort=,
                                            #   ?search=, ?team_member_id=
```

**Notes:**
- `?view=personal` returns only the user's own deals (Agent View)
- `?view=team` returns all team deals with assignee info (Team Leader View)
- `?search=` searches across client names, vendor names, companies, dates, addresses
- `?sort=urgency` (default) sorts by overdue + soonest closing first
- Pipeline `total_pipeline_value` sums purchase_price of active transactions
- Stage pills computed server-side from transaction state: `response_overdue`,
  `closing_in_X_days`, `on_track`, `in_inspection`, `pending_contract`

#### Health & System

```
GET    /api/v1/health                      # Health check
GET    /api/v1/health/ready                # Readiness check (DB connectivity)
```

### 3.3 Permission Matrix (Phase 1)

| Endpoint | Admin | TeamLead | Agent | Elf | Client | Vendor |
|----------|-------|----------|-------|-----|--------|--------|
| User management | CRUD | Read team | Read self | Read self | Read self | Read self |
| Invite users | Yes | Team only | Own elves | No | No | No |
| Create transaction | Yes | Yes | Yes | No | No | No |
| View transactions | All | Team | Own/assigned | Assigned | Own | Own |
| Manage tasks | All | Team templates | Own txn | Assigned txn | No | No |
| Task templates | System-wide | Team-wide | Personal | No | No | No |
| Upload documents | Yes | Yes | Yes | Yes | Yes (no delete) | Yes (own) |
| Delete documents | Yes | Yes | Yes | Yes | Flag only | No |
| View documents | All | Team | Own txn | Assigned txn | Own txn | Own uploads |
| Dashboard aggregation | All | Team + personal toggle | Own | Assigned | Own | No |
| Confidence settings | Global floor | Team threshold | No | No | No | No |
| Audit logs | Full | Team | No | No | No | No |

---

## 4. Frontend UI/UX Design

### 4.1 Design System (Client-Approved Redesign)

**Visual approach:** Clean, modern, minimal — dark sidebar + light content surface.
**Reference:** `data/velvet-elves-redesign.html` (client-approved Agent dashboard mockup)

- **Colors — Full semantic token system (CSS variables, white-label propagation):**
  ```css
  /* Brand */
  --brand-green: #1a9e72;          /* primary CTA, success, on-track */
  --brand-green-light: #e8f7f2;    /* AI button bg, success tint */
  --brand-green-mid: #c0ead8;      /* expanded card border, contact avatars */
  --brand-green-dark: #0f7052;     /* dark hover states */

  /* Semantic status — each has a foreground + background variant */
  --status-critical: #e53b3b;      --status-critical-bg: #fef0f0;
  --status-warning: #d97706;       --status-warning-bg: #fffbeb;
  --status-success: #1a9e72;       --status-success-bg: #e8f7f2;
  --status-info: #3b82f6;          --status-info-bg: #eff6ff;
  --status-neutral: #6b7280;       --status-neutral-bg: #f3f4f6;

  /* Surfaces */
  --surface-bg: #f7f8fa;           /* page background */
  --surface-card: #ffffff;         /* card/widget background */
  --surface-sidebar: #111827;      /* sidebar background */
  --surface-sidebar-hover: #1f2937;/* sidebar hover/active states */
  --surface-border: #e5e7eb;       /* default borders */
  --surface-border-strong: #d1d5db;/* checkbox borders, dividers */

  /* Typography */
  --text-primary: #111827;
  --text-secondary: #6b7280;
  --text-tertiary: #9ca3af;
  --text-inverse: #ffffff;
  --text-brand: #1a9e72;
  ```
  Status pills use background-tint + border + text approach (not solid fills)
  for readability while left-edge indicator bars carry urgency weight.
- **Typography:** DM Sans font family (DM Mono for numbers, dates, countdowns)
- **Layout:** Dark sidebar (240px) + header bar (60px) + main content area
- **Components:** shadcn/ui + custom components matching redesign patterns
- **Responsive:** Desktop-first with mobile breakpoints

### 4.2 Page Structure

```
App
├── Auth (public)
│   ├── Login
│   ├── Register
│   ├── Forgot Password
│   ├── Reset Password
│   ├── OAuth Callback
│   └── Invite Accept
│
├── Onboarding (protected, standalone)
│   └── OnboardingWizard (step-by-step setup)
│
├── Main App (protected, with dark sidebar)
│   │
│   │── Sidebar Navigation (per redesign):
│   │   ├── Workspace section:
│   │   │   ├── Dashboard (role-specific, with Team Lead toggle)
│   │   │   ├── Active Deals (transaction list, badge: deal count)
│   │   │   ├── Deadlines (cross-deal deadline view, badge: overdue count)
│   │   │   ├── Documents (cross-transaction view)
│   │   │   ├── Contacts (directory + vendor list)
│   │   │   └── Messages (cross-deal messages, badge: unread count)
│   │   ├── Reports section:
│   │   │   ├── Pipeline (pipeline analytics + charts)
│   │   │   └── Settings (account + team)
│   │   ├── [+ New Transaction] (pinned CTA at sidebar footer)
│   │   └── User profile (avatar initials, name, role)
│   │
│   ├── Dashboard
│   │   ├── Agent/Elf view (redesign layout)
│   │   └── Team Lead view (toggle: Team Leader / Agent)
│   │
│   ├── Active Deals / Transactions
│   │   ├── List (filterable, sortable, searchable data table)
│   │   ├── New Transaction (wizard or manual form)
│   │   └── Detail
│   │       ├── Overview Tab (transaction log)
│   │       ├── Tasks Tab (task list with status)
│   │       ├── Documents Tab (document center)
│   │       ├── Parties Tab (contacts for this deal)
│   │       └── Communications Tab (log view)
│   │
│   ├── Deadlines (cross-transaction deadline/task view)
│   │   ├── Today's Tasks
│   │   ├── All Tasks (filterable)
│   │   └── By Vendor ("vendor carts")
│   │
│   ├── Messages (cross-transaction communication view)
│   │
│   ├── Profile
│   │   ├── Personal Info
│   │   ├── Agent Bio
│   │   ├── Notification Preferences
│   │   └── Integrations (Gmail/Outlook connection)
│   │
│   └── Admin (Admin only)
│       ├── User Management
│       ├── Task Templates
│       │   ├── Master Library
│       │   └── Import from CSV
│       ├── Confidence Settings
│       ├── Tenant/Brokerage Settings
│       └── Audit Logs
│
└── Client Portal (Client role — simplified view)
    ├── My Transactions
    ├── Documents
    ├── Milestones
    └── Agent Info
```

### 4.3 Key UI Components (Phase 1)

#### 4.3.1 Agent/Elf Dashboard (Client-Approved Redesign)

**Reference:** `data/velvet-elves-redesign.html`

```
┌─────────────────┬──────────────────────────────────────────────────────┐
│  DARK SIDEBAR    │  HEADER BAR                                          │
│  ┌─────────────┐ │  Good afternoon, Jake   Mon, Mar 2 · 9 active txns  │
│  │ 🏠 Velvet   │ │  ┌─ Status Ribbon (always visible) ──────────────┐  │
│  │ Elves [AI]  │ │  │ ● 4 overdue │ ● 5 due tmrw │ ● 3 closing    │  │
│  ├─────────────┤ │  │             │ ● 2 unread messages             │  │
│  │TODAY'S TRIAGE│ │  └──────────────────────────────────────────────┘  │
│  │ 4 Overdue   │ │  [🔍 Search deals, contacts, docs] [✨ 250 AI] 🔔  │
│  │ 5 Due Tmrw  │ ├──────────────────────────────────────────────────────┤
│  │ 9 Active    │ │                                                      │
│  │ 3 Closing   │ │  ┌── Pipeline Strip (4 cards, above the fold) ────┐  │
│  ├─────────────┤ │  │ [3 Closing] [4 Inspection] [9 Active] [2 Pend] │  │
│  │ ⊞ Dashboard │ │  └────────────────────────────────────────────────┘  │
│  │ 🏘 Deals  9 │ │                                                      │
│  │ 📅 Deadlines│ │  ┌─ LEFT COLUMN ─────────┐ ┌─ RIGHT (340px) ──────┐ │
│  │ 📄 Documents│ │  │ Active Transactions    │ │ ⌛ Upcoming Closings │ │
│  │ 👥 Contacts │ │  │ [Filter chips] [Search]│ │ [4d] Connors  Mar 6  │ │
│  │ 💬 Messages │ │  │ [Sort: Urgency]        │ │ [17d] Young   Mar 19 │ │
│  ├─────────────┤ │  │                        │ │ [26d] Delgado Mar 28 │ │
│  │ 📊 Pipeline │ │  │ ┌─ Txn Card (expand) ─┐│ ├─────────────────────┤ │
│  │ ⚙ Settings  │ │  │ │▌Name │Stage│Timeline││ │ ✅ Needs Attention  │ │
│  ├─────────────┤ │  │ │▌Addr │Pill │●──●──○ ││ │ ○ Submit insp resp  │ │
│  │[+ New Txn]  │ │  │ │     Next Date  Badges││ │ ○ Request credits   │ │
│  ├─────────────┤ │  │ └─ Expanded body: ─────┘│ │ ○ Confirm walkthru  │ │
│  │ JS Agent    │ │  │   Tasks│Dates│Contacts  │ │ ✓ Clear-to-close    │ │
│  └─────────────┘ │  │   [AI Assist] [Upload]  │ └─────────────────────┘ │
│                   │  └────────────────────────┘                          │
└─────────────────┴──────────────────────────────────────────────────────┘
```

**Key design patterns:**
- **Sidebar triage grid** (2x2): overdue/due tomorrow/active/closing — visible on every page
- **Header status ribbon**: persistent summary, never scrolls away
- **Pipeline strip**: 4 color-accented cards above the fold with contextual subtitles
- **Collapsible transaction cards**: left-edge color indicator for rapid triage scanning,
  inline milestone timeline (done/current/upcoming/overdue dots), expand for 3-column
  detail (tasks with checkboxes, key dates, contacts with call/email)
- **Filter chip bar**: All, Overdue, Closing Soon, In Inspection, Pending (with live counts)
- **Transaction search bar**: next to Sort control, searches client names, vendor names,
  companies, dates, addresses, and all transaction fields
- **Sort default**: "Urgency" (most overdue + soonest closing first)
- **Right column widgets**: closing countdown tiles (urgent/soon/normal coloring),
  cross-deal "Needs Attention Today" task list with deal links
- **Contextual AI actions** per card: "Summarize this deal", "Draft inspection response",
  "Closing checklist"
- **Section header badge**: "X need attention" count next to "Active Transactions" title
- **View All links**: each section/widget has a "View All →" link to the full page
- **Nav active state**: green left-edge bar (3px) on active sidebar link
- **Notification bell**: badge count in header, hidden when 0
- **Card hover**: subtle box-shadow on hover; green border + shadow on expand
- **Inline task completion**: checkbox directly in expanded card; overdue tasks get red
  checkbox border, warning tasks get amber border, completed get green fill with checkmark

#### 4.3.1b Team Lead Dashboard

```
┌───────────────────────────────────────────────────────────┐
│  Dashboard                                                 │
│  ┌─────────────────────────────────────────────┐           │
│  │ [Team Leader View]  [Agent View]  ← toggle  │           │
│  └─────────────────────────────────────────────┘           │
│                                                             │
│  Team Leader View:                                          │
│  - Same layout as Agent dashboard                           │
│  - Triage numbers reflect team-wide totals                  │
│  - Pipeline strip aggregates across team members            │
│  - Transaction cards include assignee name                  │
│  - Filter by team member (dropdown) + standard filters      │
│  - Team task template management access                     │
│  - Activity log overview for all team transactions          │
│                                                             │
│  Agent View:                                                │
│  - Identical to Agent dashboard (personal deals only)       │
│  - TL's own transactions and tasks                          │
└───────────────────────────────────────────────────────────┘
```

**Why toggle:** Most Team Leads also sell real estate and need both a personal
agent view (their own deals) and a team oversight view (all team deals).

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

  // Main app — sidebar navigation (per redesign)
  DASHBOARD: '/dashboard',
  PROFILE: '/profile',

  // Workspace section
  ACTIVE_DEALS: '/deals',                    // NEW: sidebar "Active Deals"
  TRANSACTIONS: '/transactions',             // alias for /deals (backward compat)
  NEW_TRANSACTION: '/transactions/new',
  TRANSACTION_DETAIL: '/transactions/:id',

  DEADLINES: '/deadlines',                   // NEW: sidebar "Deadlines"
  TASKS: '/tasks',                           // cross-transaction task view
  TASK_DETAIL: '/tasks/:id',

  DOCUMENTS: '/documents',

  CONTACTS: '/contacts',
  CONTACT_DETAIL: '/contacts/:id',

  MESSAGES: '/messages',                     // NEW: sidebar "Messages"

  // Reports section
  PIPELINE: '/pipeline',                     // NEW: sidebar "Pipeline"
  SETTINGS: '/settings',

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

```
React Query (TanStack Query)
├── Server State (cached via React Query)
│   ├── /auth/me                    → current user
│   ├── /dashboard/triage           → sidebar triage counts (NEW)
│   ├── /dashboard/status-ribbon    → header ribbon counts (NEW)
│   ├── /dashboard/pipeline-summary → pipeline strip cards (NEW)
│   ├── /dashboard/upcoming-closings→ closing countdown widget (NEW)
│   ├── /dashboard/needs-attention  → cross-deal task widget (NEW)
│   ├── /dashboard/transaction-cards→ collapsible card data (NEW)
│   ├── /transactions               → transaction list
│   ├── /tasks                      → task list
│   ├── /contacts                   → contact directory
│   ├── /documents                  → documents
│   ├── /task-templates             → template library
│   └── /audit-logs                 → audit trail
│
├── Client State (React Context)
│   ├── AuthContext        → JWT token, user session
│   ├── ThemeContext       → white-label branding (NEW)
│   ├── DashboardViewContext → Team Lead toggle state (NEW)
│   └── NotificationContext → toast/alert state
│
└── Form State (React Hook Form)
    ├── TransactionForm
    ├── TaskTemplateForm
    ├── ContactForm
    └── UserInviteForm
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
2. Update route constants for new pages
3. Plan component structure

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
- `transactions`: minimal fields → needs full expansion
- `tasks`: basic fields → needs template_id, target, AI fields
- `documents`: basic fields → needs versioning, classification, signature tracking
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
- **More granular roles** (6 vs ListedKit's simpler model)
- **AI email automation** with safeguards (ListedKit has basic drafting)
- **Vendor communication system** with structured responses
- **White-label multi-tenancy** (ListedKit is single-brand)
- **Advertising module** for monetization
- **Task dependency engine** (more sophisticated than ListedKit's checklists)
