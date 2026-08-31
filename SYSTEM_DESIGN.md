# Velvet Elves - System Design Document

**Date:** 2026-03-05
**Last Updated:** 2026-08-25 (as-built sync with velvet-elves-backend and velvet-elves-frontend)
**Scope:** Live architecture across all shipped phases — multi-tenant FastAPI + React SPA, AI wizard, transaction workspace, Aime automation, Stripe billing, platform admin, Help Center, and marketing lead capture. Original Phase 1 schema remains the foundation; this document now describes the as-built system, not the Week 1 plan.
**Reference:** ListedKit.com as early design benchmark; FRONTEND_UI_WORKFLOW_LOGIC.md as canonical frontend specification; requirements.txt §15 for client-confirmed generation rules

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Database Schema Design](#2-database-schema-design)
3. [API Architecture](#3-api-architecture)
4. [Frontend UI/UX Design](#4-frontend-uiux-design)
5. [Phase 1 Implementation Plan (historical)](#5-phase-1-implementation-plan)

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENTS                                    │
│   React SPA (Vite + TypeScript)                                   │
│   Help Center SPA · Marketing website SPA · Future Mobile App     │
└──────────────┬───────────────────────────────────────────────────┘
               │ HTTPS / JWT (Supabase Auth)
┌──────────────▼───────────────────────────────────────────────────┐
│              AWS (ECS Fargate + ECR + CloudFront)                  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              FastAPI Application Server                      │  │
│  │  ┌──────────┐  ┌───────────┐  ┌────────────┐  ┌──────────┐ │  │
│  │  │ Routers  │→ │ Services  │→ │Repositories│→ │ Supabase │ │  │
│  │  │ (API v1) │  │ (Business │  │ (Data      │  │ Client   │ │  │
│  │  │          │  │  Logic)   │  │  Access)   │  │          │ │  │
│  │  └──────────┘  └───────────┘  └────────────┘  └──────────┘ │  │
│  │  ┌──────────┐  ┌───────────┐  ┌────────────┐  ┌─────────┐ │  │
│  │  │   Auth   │  │ AI Engine │  │ Task Engine│  │ Billing │ │  │
│  │  │Middleware│  │(Multi-AI) │  │+ Aime      │  │ Stripe  │ │  │
│  │  └──────────┘  └───────────┘  └────────────┘  └─────────┘ │  │
│  └─────────────────────────────────────────────────────────────┘  │
│  EventBridge → POST /api/v1/internal/schedules/tick               │
└──────────────┬───────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────┐
│  SUPABASE          AWS            STRIPE         SENDGRID         │
│  PostgreSQL        Textract+S3    Invoices       Platform mail    │
│  Auth (GoTrue)     (OCR)          Deal-fee       (welcome/alerts) │
│  Storage buckets                  Credits                         │
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
| Database | Supabase PostgreSQL | Auth + DB + Storage unified |
| Data Access | supabase-py (PostgREST) | No ORM; aligns with Supabase |
| Auth | Supabase Auth (GoTrue) + JWT, wrapped by FastAPI `/api/v1/users/*` | No `/api/v1/auth` router; passwords never stored in app DB |
| Multi-tenancy | tenant_id + app-layer isolation | RLS policies exist but are dormant; service role bypasses RLS |
| PII | Fernet encryption at rest | email, full_name, phone, address encrypted in repositories |
| AI | OpenAI GPT **or** Anthropic Claude (switchable) + Amazon Textract OCR | Provider-agnostic factory; tenant `settings_json.ai_provider` |
| File Storage | Supabase Storage | Signed URLs; documents bucket |
| Hosting | AWS ECS Fargate + ECR; CloudFront for SPAs | Stage and prod; Secrets Manager |
| Platform mail | SendGrid HTTP API | Welcomes, invites, registration alerts — not SES |
| User mailboxes | Gmail, Outlook, iCloud | OAuth (Gmail/Outlook) or app-password (iCloud) |
| E-sign | DocuSign | HelloSign not wired |
| Payments | Stripe | Client invoices + public pay links + $49/deal credit wallet |
| Frontend State | React Query (TanStack) | Server state caching, mutations, optimistic updates |
| UI Components | shadcn/ui + Tailwind | Design system; tokens in `src/index.css` |

### 1.4 Multi-Tenant Architecture

```
Tenant (Brokerage)
  └── Users (Agent, TransactionCoordinator, TeamLead, Attorney, Admin,
             Client, ForSaleByOwner, Vendor)
       + is_platform_admin (flag, not a role)
       + tenant owner (tenants.owner_user_id)
       └── Transactions
            ├── Tasks
            ├── Documents / requirements / templates
            ├── Contacts / parties / vendor assignments
            ├── Communication logs + AI drafts
            └── Invoices / payments
```

- Every data table has `tenant_id` column
- Tenant isolation is enforced in FastAPI services; RLS policies exist in SQL but are **dormant** (API uses the service role)
- Tenant configuration stores branding (logo, colors, domain)
- Admin users and tenant owners manage tenant-level settings; platform admins use `/platform/*`

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

**AI Provider Config:** `settings_json` stores the active AI provider preference. Example structure:
```json
{
  "ai_provider": "openai",       // "openai" | "claude"
  "ai_provider_config": {
    "openai_model": "gpt-5.4",
    "claude_model": "claude-sonnet-4-20250514"
  }
}
```
Admin users can switch the active provider (`ai_provider`) at any time via system settings. All AI features (document parsing, email automation, task suggestions, wizard logic) route through a provider-agnostic abstraction layer that reads this setting. Audit logs record which provider was used for each AI action.

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
    TRANSACTION_COORDINATOR = "TransactionCoordinator"  # UI: Transaction Coordinator (historically "Elf")
    TEAM_LEAD = "TeamLead"
    ATTORNEY = "Attorney"
    ADMIN = "Admin"
    CLIENT = "Client"
    FOR_SALE_BY_OWNER = "ForSaleByOwner"  # UI: For Sale By Owner
    VENDOR = "Vendor"
# Platform admin is users.is_platform_admin (bool), not a role.
# Tenant owner is tenants.owner_user_id == users.id (computed is_tenant_owner).

class TransactionUseCase(str, enum.Enum):
    BUY_FIN = "Buy-Fin"
    BUY_CASH = "Buy-Cash"
    SELL_FIN = "Sell-Fin"
    SELL_CASH = "Sell-Cash"
    BOTH_FIN = "Both-Fin"
    BOTH_CASH = "Both-Cash"

class TransactionStatus(str, enum.Enum):
    ACTIVE = "Active"
    INCOMPLETE = "Incomplete"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    CLOSED = "Closed"
    TERMINATED = "Terminated"

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

class ClosingMode(str, enum.Enum):
    ATTORNEY = "attorney"
    TITLE_ESCROW = "title_escrow"
    SHARED_APPROVAL = "shared_approval"

class FSBOState(str, enum.Enum):
    LISTING_PREP = "listing_prep"
    UNDER_CONTRACT = "under_contract"
```

Document types, contact types, and communication channels match `app/models/enums.py` (includes attorney packet types, addendum, lead-paint, listing photos, wire authorization, SMS/voice_call hooks).

Self-signup roles (`SELF_SIGNUP_ROLES_NOW`): Agent, TeamLead, TransactionCoordinator, Admin.

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
-- Note: Service role key bypasses RLS for backend operations.
-- As-built: FastAPI uses the service role; tenant isolation is enforced
-- in services/repositories. RLS activation for client-direct access is
-- still a hardening item.
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

### 2.6 Tables added after Phase 1 (as-built catalog)

The live schema is additive across ~117 Supabase migrations. Milestone 5.3 profile tables (`profile_resources`, `profile_checklist_templates`, etc.) were **dropped**; playbook data lives in `users.profile_settings_json` and `/api/v1/me/*`.

| Domain | Tables |
|--------|--------|
| Tenants / users | `tenants` (owner, plan, domain, deletion lifecycle), `workspace_memberships`, invitation + notification prefs on `users` (`is_platform_admin`, `deactivated_at`) |
| Transactions | `transaction_field_corrections`, `transaction_briefs`, `user_metric_snapshots`; transactions gained `title_ordered_by`, `has_appraisal`, attorney-review columns, `deadline_day_basis_json`, `earnest_money_days`, `fees_json` |
| Tasks | `task_templates.workflow` (`any` / `title_escrow` / `attorney`), attorney task library seeds |
| Documents | `document_ocr_geometry`, `document_templates`, `document_requirement_templates`, `transaction_document_requirements`, priority waivers/flags/events |
| Comms | `communication_log_views`, `email_templates`, `inbound_sender_deal_links`, `inbound_filtered`, `inbound_suppression_rules`, `notifications` |
| Payments | `stripe_customers`, `invoices`, `invoice_line_items`, `payments`, `refunds`, `commission_payouts` (parked), `payment_access_policy`, `credit_wallets`, `credit_ledger`, `credit_purchases`, `platform_settings` |
| Vendors | `vendor_email_templates`, `transaction_vendor_assignments` (+ contacts), `vendor_proposals`, `vendor_colleague_tokens`, `vendor_background_refreshes`, `vendor_task_actions` |
| AI / Aime | `wizard_runs`, `ai_usage_events`, `ai_suggestions`, `agent_threads`, `agent_messages`, `agent_actions`, `agent_action_rules` |
| Attorney | `attorney_review_items`, `attorney_packet_releases` |
| Platform | `platform_audit`, `platform_archive`, `platform_legal_holds`, `tenant_deletion_runs`, `tenant_api_keys`, `tenant_webhooks`, `webhook_deliveries`, `service_cost_daily` |
| Help / ads / misc | `help_collections`, `help_articles` (+ related/feedback/revisions), `advertising_hooks`, `ad_packages`, `ad_orders`, `calendar_event_links`, `milestone_share_links`, `marketing_leads` |

RLS note: policies in §2.4 are designed; the API uses the service role and enforces tenant isolation in services. Activating RLS for client-direct access remains a hardening item (requirements §12.14).

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

### 3.2 As-built API Endpoints

All paths are under `/api/v1`. **There is no `/api/v1/auth` router.** Login, register, refresh, password-reset, OAuth, and `/me` live on `/api/v1/users/*`. Invitations live on `/api/v1/invitations`. OpenAPI is served at `/api/docs` outside production.

#### Auth & Users (`/api/v1/users`)

```
POST   /api/v1/users/email-available
POST   /api/v1/users/register
POST   /api/v1/users/login                 # OAuth2 token URL
POST   /api/v1/users/refresh
POST   /api/v1/users/confirm-email
POST   /api/v1/users/oauth/{provider}/start
POST   /api/v1/users/oauth/{provider}/exchange
POST   /api/v1/users/password-reset/request
POST   /api/v1/users/password-reset/confirm
GET    /api/v1/users/me
PATCH  /api/v1/users/me
GET    /api/v1/users/me/workspaces
GET    /api/v1/users
GET    /api/v1/users/assignable
GET    /api/v1/users/{user_id}
PUT    /api/v1/users/{user_id}/role
DELETE /api/v1/users/{user_id}

POST   /api/v1/invitations
GET    /api/v1/invitations
GET    /api/v1/invitations/verify/{token}
POST   /api/v1/invitations/accept/{token}
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

# Milestone 4.3 — per-transaction vendor assignments + opted-in contacts
GET    /api/v1/transactions/{id}/vendor-assignments
POST   /api/v1/transactions/{id}/vendor-assignments
PUT    /api/v1/transactions/{id}/vendor-assignments/{assignId}
PUT    /api/v1/transactions/{id}/vendor-assignments/{assignId}/contacts
DELETE /api/v1/transactions/{id}/vendor-assignments/{assignId}
```

#### Vendor Communications (`/api/v1/vendor-communications`) — Milestone 4.3

```
GET    /api/v1/vendor-communications/templates             # List active templates
POST   /api/v1/vendor-communications/templates             # Admin: create custom
PUT    /api/v1/vendor-communications/templates/{id}        # Admin: edit
DELETE /api/v1/vendor-communications/templates/{id}        # Admin: deactivate

POST   /api/v1/vendor-communications/preview               # Render only (no send)
POST   /api/v1/vendor-communications/send                  # Render + send via provider

GET    /api/v1/vendor-communications/proposals             # List pending proposals
GET    /api/v1/vendor-communications/proposals/{id}        # Proposal detail
POST   /api/v1/vendor-communications/proposals/{id}/accept # Update task.due_date
POST   /api/v1/vendor-communications/proposals/{id}/reject
POST   /api/v1/vendor-communications/proposals/{id}/needs-clarification

GET    /api/v1/vendor-communications/settings              # Tenant settings
PUT    /api/v1/vendor-communications/settings
```

#### Vendor extensions (`/api/v1/vendors`) — Milestone 4.3

```
GET    /api/v1/vendors/{id}/transactions                   # Read-only portfolio
POST   /api/v1/vendors/{id}/colleague-invites              # Create public invite
GET    /api/v1/vendors/{id}/colleague-invites              # List active invites
DELETE /api/v1/vendors/colleague-invites/{inviteId}        # Revoke by id

POST   /api/v1/vendors/{id}/background-refresh             # Queue suggestion run
GET    /api/v1/vendors/{id}/background-refresh             # Latest run + suggestions
POST   /api/v1/vendors/{id}/background-refresh/apply       # Apply selected fields
```

#### Public vendor (`/api/v1/public/vendor`) — Milestone 4.3, no auth

```
GET    /api/v1/public/vendor/colleague-invites/{token}         # Validate
POST   /api/v1/public/vendor/colleague-invites/{token}/accept  # Single-use accept
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

#### Confidence Settings (`/api/v1/confidence`)

```
GET    /api/v1/confidence                  # Get current tenant/team floors
PUT    /api/v1/confidence/tenant           # Admin
PUT    /api/v1/confidence/team/{team_id}   # Team override (cannot go below tenant floor)
```

#### AI Provider Settings (`/api/v1/settings/ai-provider`)

```
GET    /api/v1/settings/ai-provider        # Get active AI provider & config
PUT    /api/v1/settings/ai-provider        # Switch provider: { "ai_provider": "openai" | "claude" } (Admin only)
```

#### Audit Logs (`/api/v1/audit-logs`)

```
GET    /api/v1/audit-logs                  # List audit logs (Admin only)
GET    /api/v1/audit-logs/{entityType}/{entityId} # Logs for specific entity
```

#### Shared dashboard aggregations (`/api/v1/dashboard`) — not `/workspace`

```
GET    /api/v1/dashboard/ai-briefing
GET    /api/v1/dashboard/sidebar-kpis
GET    /api/v1/dashboard/deal-state-counts
GET    /api/v1/dashboard/transaction-tab-counts
GET    /api/v1/dashboard/transaction-cards
GET    /api/v1/dashboard/documents-ai-briefing
GET    /api/v1/dashboard/documents-priority-queue
POST   /api/v1/dashboard/ai-chat

GET    /api/v1/dashboard/agent            # Solo Agent aggregate
GET    /api/v1/dashboard/team
GET    /api/v1/dashboard/attorney
GET    /api/v1/dashboard/admin
GET    /api/v1/dashboard/fsbo/overview
GET    /api/v1/dashboard/client
GET    /api/v1/dashboard/vendor

PUT    /api/v1/transactions/{id}/key-dates
GET    /api/v1/transactions/{id}/history
GET    /api/v1/transactions/{id}/plan
GET    /api/v1/automation/needs-you
```

#### Additional as-built routers (summary)

| Prefix | Purpose |
|--------|---------|
| `/onboarding` | Status, company, logo, complete |
| `/integrations` | Gmail / Outlook / iCloud / DocuSign OAuth, CRM keys |
| `/documents` | Upload, versions, OCR geometry, e-sign, flag-deletion, generate-from-template |
| `/document-templates` | Fillable PDF library |
| `/wizard-runs` | Cross-device wizard drafts |
| `/ai` | Parse, recommend, suggestions, wizard-command |
| `/ai-emails` | Drafts, approve/edit-and-send, inbound filter |
| `/automation` | Tenant posture, needs-you, run-now |
| `/agent/rules` | Always-approve rules |
| `/confidence` | Tenant/team floors (`GET /confidence`, `PUT /confidence/tenant`) |
| `/esign` | DocuSign send/status/webhooks |
| `/invoices`, `/payments`, `/billing/credits`, `/public/pay` | Stripe lanes |
| `/calendar` | Google / Outlook calendar |
| `/search` | Global search |
| `/notifications` | In-app + prefs + digest |
| `/vendor-portal` | Vendor Files / Documents / Tasks |
| `/client/*` | Messages, invoices, document ack |
| `/attorney` | Approve, release-packet, matters, state-rules, recording-calendar |
| `/milestones/shared/{token}` | Public milestone viewer |
| `/platform/*` | Tenants, users, billing, costs, AI usage, help, ads, waitlist |
| `/public/help`, `/public/marketing`, `/public/ads`, `/public/tenant-branding` | Public SPAs |
| `/me` | Playbook (checklists, notes, vendors, resources) |
| `/ads`, `/admin/advertising` | In-app ads |
| `/internal/schedules/tick` | EventBridge scheduler |

**Notes:**
- Dashboard landing pages reuse `/dashboard/*` aggregations
- Key dates are editable via `PUT /transactions/{id}/key-dates`
- Transaction history merges audit + comms + task events
- AI chat is `POST /dashboard/ai-chat` (not `/workspace/ai-chat`)
- Confidence settings are `/confidence`, not `/settings/confidence`

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
                                            #   properties[], critical_next_steps[] (derived
                                            #   from missing docs / dates / tasks — never
                                            #   hardcoded), days_to_close_nearest,
                                            #   share_links_live, missing_documents_count,
                                            #   recent_milestones[], ai_guidance,
                                            #   support_contact, boundary_notice
GET    /api/v1/dashboard/fsbo/properties/{transaction_id}
                                            # Property detail (ownership-checked — cross-owner
                                            #   returns 404, never confirms existence):
                                            #   address (decrypted), fsbo_state, closing_date,
                                            #   days_to_close, key_dates[], milestones[]
                                            #   (timeline with done/active/upcoming), document_board
                                            #   (Missing/InProgress/Uploaded/Verified/Complete),
                                            #   documents[], share_links[], messages[]
                                            #   (portal-visible coordinator messages only),
                                            #   ai_guidance, support_contact, boundary_notice
GET    /api/v1/dashboard/fsbo/documents     # FSBO document board projection:
                                            #   per-property board where Missing = absence of a
                                            #   required doc_type for the property's fsbo_state;
                                            #   Verified vs Complete = signature-in-flight rule.
                                            #   totals[] aggregates across all owned properties.
GET    /api/v1/dashboard/fsbo/milestones    # Milestones & messages:
                                            #   properties[] with per-property milestone timeline
                                            #   and key dates; messages[] = portal-visible
                                            #   coordinator messages (excludes internal notes,
                                            #   AI-draft internals, document-action events).
GET    /api/v1/dashboard/fsbo/share-link    # Milestone sharing (FSBO scoped to owned tx):
POST   /api/v1/dashboard/fsbo/share-link    #   create/manage expirable read-only links;
DELETE /api/v1/dashboard/fsbo/share-link/{link_id}
                                            #   revoke — `assert_fsbo_transaction_access`
                                            #   blocks cross-owner list/create/revoke.
```

#### AI Suggestions (`/api/v1/ai/suggestions`)

```
GET    /api/v1/ai/suggestions              # List pending AI suggestions
                                           #   type, title, description, transaction_id,
                                           #   confidence, source, reason, suggested_action
                                           #   Supports: ?type=task_add|task_remove|deadline_adjust|
                                           #     email_draft|document_request|risk_alert,
                                           #   ?min_confidence=0.75, ?transaction_id=
GET    /api/v1/ai/suggestions/stats        # Summary: pending count, accepted/rejected this week,
                                           #   confidence distribution
POST   /api/v1/ai/suggestions/{id}/accept  # Accept suggestion: { scope: 'transaction'|'all_future' }
POST   /api/v1/ai/suggestions/{id}/dismiss # Dismiss suggestion: { reason: 'optional text' }
```

#### Analytics (`/api/v1/analytics`)

```
GET    /api/v1/analytics/dashboard         # Aggregated analytics:
                                           #   closings_by_month, revenue_trend,
                                           #   task_completion_rates, avg_days_to_close,
                                           #   transaction_type_distribution,
                                           #   ai_suggestion_acceptance_rate, drift_reasons
                                           #   Supports: ?period=month|quarter|year|custom,
                                           #   ?start=, ?end=, ?agent_id= (team view)
```

#### Notifications (`/api/v1/notifications`)

```
GET    /api/v1/notifications               # List notifications for current user
                                           #   Supports: ?read=true|false, ?page=, ?limit=
PUT    /api/v1/notifications/{id}/read     # Mark notification as read
PUT    /api/v1/notifications/read-all      # Mark all as read
GET    /api/v1/notifications/preferences   # Get notification preferences
PUT    /api/v1/notifications/preferences   # Update preferences (per-channel toggles)
```

#### Task Queue (`/api/v1/tasks/queue`)

```
GET    /api/v1/tasks/queue                 # Personal task queue:
                                           #   Supports: ?assignee=me|team,
                                           #   ?filter=overdue|due_today|upcoming|completed,
                                           #   ?sort=urgency|due_date|transaction|status,
                                           #   ?group_by=vendor (vendor cart view)
```

#### Attorney Actions (`/api/v1/attorney`)

```
POST   /api/v1/attorney/approve            # Sign-off on a review item:
                                           #   { matter_id, item_id, action: 'approve'|'hold' }
POST   /api/v1/attorney/release-packet     # Release a legal packet:
                                           #   { matter_id, recipients[], document_ids[] }
                                           #   ALWAYS human-initiated; no AI auto-release
PATCH  /api/v1/attorney/matters/{id}       # Update matter status (e.g., hold with reason)
GET    /api/v1/attorney/releases           # List release-ready matters
GET    /api/v1/attorney/state-rules        # State rules reference: ?state=
GET    /api/v1/attorney/recording-calendar # Recording calendar: ?start=&end=
```

#### Client Portal

```
# Canonical aggregated read — feeds all four Client surfaces (transactions +
# per-transaction milestone timeline/key-dates, document status summary, agent
# card). There are no per-surface /client/{transactions,documents,milestones}
# endpoints; the portal standardized on the /dashboard/client namespace
# (mirrors FSBO's /dashboard/fsbo decision — CLIENT_WORKSPACE_PLAN.md D3).
GET    /api/v1/dashboard/client            # Aggregated client dashboard read

# Two-way "Ask a question" thread, gated by communication_logs.is_client_visible.
POST   /api/v1/client/messages             # Client asks a question (persists + notifies assignee)
GET    /api/v1/client/messages?transaction_id=...  # Client-visible thread (questions + surfaced replies)

# Documents (view/download/upload, no delete) reuse the role-scoped document API,
# which already returns only the client's own documents:
GET    /api/v1/documents?transaction_id=...        # Client's own documents
POST   /api/v1/documents/upload                    # Upload (transaction + doc_type)
POST   /api/v1/documents/{id}/flag-deletion        # Request document deletion review
```

#### Public Milestone Viewer (`/api/v1/milestones/shared`)

```
GET    /api/v1/milestones/shared/{token}   # Public milestone data (no auth required):
                                           #   property_address, milestone_steps[],
                                           #   key_dates[], document_status_cues[]
                                           #   Returns 404 if token expired/invalid
POST   /api/v1/milestones/shared/{token}/viewed  # Record viewer-open event;
                                           #   triggers notification to link creator
```

#### Admin (`/api/v1/admin`)

```
GET    /api/v1/admin/users                 # List all users in tenant:
                                           #   ?role=, ?status=active|inactive, ?team_id=, ?search=
PATCH  /api/v1/admin/users/{id}            # Update user (role, status, team assignment)
POST   /api/v1/admin/invitations           # Send invitation: { email, role, team_id?, transaction_id? }
GET    /api/v1/admin/audit-logs            # System-wide audit log:
                                           #   ?user_id=, ?entity_type=, ?action=,
                                           #   ?date_start=, ?date_end=, ?search=
GET    /api/v1/admin/audit-logs/export     # Export filtered logs as CSV
```

#### Health & System

```
GET    /api/v1/health                      # Health check
GET    /api/v1/health/ready                # Readiness check (DB connectivity)
```

### 3.3 Permission Matrix (as-built)

| Capability | Admin | TeamLead | Agent | TC | Attorney | Client | FSBO | Vendor |
|------------|-------|----------|-------|----|----------|--------|------|--------|
| User management | CRUD | Team | Self | Self | Self | Self | Self | Self |
| Invite users | Yes | Team | Own TCs | No | No | No | No | No |
| Create transaction | Yes | Yes | Yes | Yes | No | No | No | No |
| View transactions | All | Team | Own/assigned | Assigned | Assigned matters | Own | Own properties | Assigned files |
| Transaction workspace | Full | Team | Own | Assigned | Matter workspace | Portal | Portal | Portal |
| Task templates | System | Team | Playbook | Playbook | No | No | No | No |
| Upload documents | Yes | Yes | Yes | Yes | Legal packets | No delete | No delete | Own |
| Needs You / AI emails | Yes | Yes | Yes | Yes | No (Ask AI on matter) | No | No | No |
| Approve/release packets | No | No | No | No | Yes | No | No | No |
| Confidence / AI settings | Yes | Team floor | No | No | No | No | No | No |
| Audit logs | Full | Team comms audit | No | No | Own matters | No | No | No |
| Analytics | System | Team | Own | No | No | No | No | No |
| Invoices | Per payment-access policy | | | | No | Pay own | Pay own | No |
| Platform console | Only `is_platform_admin` | | | | | | | |
| Milestone sharing | — | — | — | — | — | Yes | Yes | No |

---

## 4. Frontend UI/UX Design

### 4.1 Design System (as-built)

**Workflow Logic Reference:** The complete page-by-page frontend specification is `FRONTEND_UI_WORKFLOW_LOGIC.md` (synced 2026-08-25). That document is the canonical reference for live routes, shells, wizard phases, and workspace tabs.

**Visual approach:** B2B institutional trust pack — dark sidebar + light content surface + high-density transaction cards. Client portal uses a distinct concierge navy shell; Vendor portal uses a bright white rail; Attorney uses AttorneyLayout (caseload rail). STYLE_GUIDE.md (v2 comfort scale) governs type, contrast, and AI surfaces.

**Approved HTML design references (2026-03-26)** remain historical benchmarks in `completed_designs/`. The shipping UI has since added the deal workspace, Needs You, Settings hub, and portal shells.

**Frontend stack:** Vite + React + TypeScript; TanStack Query; React Router; Tailwind + CSS variables; shadcn/ui. Route table: `src/App.tsx` + `src/utils/constants.ts` (`ROUTES`). Role landing: `getLandingRoute` in `dashboardShellConfig.ts`.

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

### 4.2 Page Structure (as-built 2026-08-25)

Canonical route table: `FRONTEND_UI_WORKFLOW_LOGIC.md` §0. Shells: `AppLayout` (internal + FSBO variant), `AttorneyLayout`, `ClientWorkspaceLayout`, `VendorWorkspaceLayout`.

```text
App
|-- Auth (public)
|   |-- /login /register /forgot-password /reset-password
|   |-- /auth/confirm  /oauth/callback  /invite/:token
|   |-- /terms /privacy
|
|-- Onboarding (protected, standalone)
|   `-- /onboarding
|
|-- Wizard (protected, no AppLayout)
|   `-- /transactions/new          # 4 phases: Upload → Contract Details → Contacts & Fees → Verification
|
|-- Internal AppLayout (Agent, TransactionCoordinator, TeamLead, Admin)
|   |-- Topbar: briefing chip · ⌘K · bell · user · + New Transaction
|   |-- Sidebar KPIs + groups:
|   |   |-- Dashboard (role landing)
|   |   |-- Deals: Active · Drafts & Paused · Closed · All · Clients · Contacts
|   |   |-- Workflow: Needs You · Task Queue · Documents · Calendar
|   |   |-- Payments · Vendors
|   |   |-- Intelligence: Suggestions · Email · Vendor Proposals · Reports
|   |   |-- Team (TeamLead+Admin) · Oversight (Admin)
|   |   `-- Platform (is_platform_admin)
|   |-- Settings hub /settings (not a sidebar group); org at /organization
|   |-- Deal list /transactions/*  + workspace /transactions/:id
|   |   `-- Tabs: Overview, Timeline, Compliance, Tasks, Documents,
|   |       Contacts, Billing, Activity (+ Agent/Email behind flag)
|
|-- AttorneyLayout
|   |-- /dashboard/attorney → first matter or empty
|   |-- /transactions/:id AttorneyMatterWorkspacePage
|   `-- /attorney/releases · /attorney/state-rules · /attorney/recording-calendar
|
|-- FSBO (AppLayout fsbo variant)
|   `-- /fsbo · properties · documents · milestones · invoices
|       Share is a modal (no /fsbo/share)
|
|-- ClientWorkspaceLayout
|   `-- /client/home · next-steps · milestones · documents · updates
|       /client/transactions redirects to /client/home
|
|-- VendorWorkspaceLayout
|   `-- /portal/vendor · files/:id · documents · tasks
|
|-- Platform /platform/*
|
`-- Public
    |-- /milestones/:shareToken
    |-- /v/:token  /pay/invoices/:id  /advertise
```

### 4.3 Key UI Components (Phase 1 design files)

**As-built deltas vs the mocks below:** Create is `/transactions/new` (4-phase wizard), not a quick-create modal. Durable editing is `/transactions/:id` (Compliance is a tab). Filter tab **Unhealthy** is retired. Role string is TransactionCoordinator, not Elf. Settings is a hub, not a sidebar Intelligence item. Attorney landing is a redirect into a matter.

#### 4.3.1 Agent / Transaction Coordinator Active Transactions list (Client-Approved Redesign)

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
| - Tabs: All | Overdue | Due Today | Closing Soon | Needs Attention |       |
|         In Inspection | On Track                                           |
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
| - New Transaction → /transactions/new (4-phase wizard; not a modal)      |
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
  - Same topbar, sidebar, tabs, transaction-card system, and overlays as Agent/TC view
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

**Workspace isolation (2026-08-15):** Attorney is not an Agent with extra
legal buttons. Direct URL access to All Documents (`/documents`), the closing
calendar (`/calendar`), Contacts, AI Suggestions, Analytics, and the AI email
outbox is denied. Search and notifications stay on assigned matters. Counsel
Ask AI replaces the Agent Suggestions page. Document review happens on the
matter workspace, not the All Documents queue.

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

### 4.4 Live frontend routes (2026-08-25)

Source of truth: `velvet-elves-frontend/src/utils/constants.ts` (`ROUTES`) and `src/App.tsx`. Condensed:

```
Auth:     /login /register /forgot-password /reset-password
          /auth/confirm /oauth/callback /invite/:token /terms /privacy
Wizard:   /transactions/new
Dash:     /dashboard → getLandingRoute(user)
          /dashboard/agent | /team | /attorney (redirect to matter) | /admin
Deals:    /transactions /transactions/active|pending|closed|all
          /transactions/:id
Workflow: /needs-you /tasks/queue /documents /calendar /clients /contacts
Intel:    /ai-suggestions /ai-emails /vendor-proposals /reports
Pay:      /payments  /payments/payouts
Settings: /settings  /settings/account|notifications|connections|my-playbook
          |document-templates|help
          /organization
Attorney: /attorney/releases | state-rules | recording-calendar
          /attorney/queue → /transactions/active
FSBO:     /fsbo /fsbo/properties /fsbo/documents /fsbo/milestones /fsbo/invoices
Client:   /client/home /next-steps /milestones /documents /updates
          /client/transactions → /client/home
Vendor:   /portal/vendor /portal/vendor/files/:id /documents /tasks
Platform: /platform/tenants|users|waitlist|ai-usage|costs|billing|help|advertising
Public:   /milestones/:token /v/:token /pay/invoices/:id /advertise
Retired:  /profile → /reports?scope=me   /communications → /admin/communications
          /fsbo/share (modal)   /closing-calendar (use /calendar)
```

### 4.5 Frontend State Architecture

```text
React Query (TanStack Query) — keys in src/utils/constants.ts QUERY_KEYS
|-- Server State
|   |-- GET /users/me                     -> current user
|   |-- GET /dashboard/ai-briefing        -> topbar briefing
|   |-- GET /dashboard/sidebar-kpis       -> sidebar KPI tiles
|   |-- GET /dashboard/deal-state-counts  -> Active / Drafts / Closed / All
|   |-- GET /dashboard/transaction-cards  -> collapsible card data
|   |-- GET /dashboard/agent|team|attorney|admin|fsbo/*|client|vendor
|   |-- GET /wizard-runs/current          -> wizard draft
|   |-- GET /automation/needs-you
|   |-- GET /transactions /tasks /contacts /documents
|   |-- GET /ai/suggestions  /ai-emails  /analytics
|   |-- GET /invoices /payments /billing/credits
|   |-- GET /vendor-portal/*
|   `-- GET /milestones/shared/:token
|
|-- Client State (React Context)
|   |-- AuthContext
|   |-- ThemeContext (white-label)
|   |-- IntakeContext (file drop → wizard)
|   |-- FsboShareContext (share modal)
|   |-- TourProvider
|   `-- Notification / toast
```

---

## 5. Phase 1 Implementation Plan

**Historical Week 1–3 checklist.** Completion status lives in `milestones.txt` (STATUS lines + PHASE 8). Unchecked boxes below are **not** current work; they were the original plan. Hosting is ECS Fargate, not a long-lived EC2 app server. Auth is `/api/v1/users/*`.

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
