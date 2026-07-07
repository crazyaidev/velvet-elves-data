# Platform Cost & Pricing Analytics Console - Implementation Plan

Date: 2026-07-07 (Rev 2, same day)
Status: PLAN ONLY. No source code has been changed. Every claim about the
current system below was verified by reading the actual source before writing
this plan.

Rev 2 review corrections (each verified against source, see §1.5/§2/§3):

- R1. `/ai/intake/classify` and `/ai/parse-checklist` are deterministic (no
  LLM call at all); removed from the attribution work. The `intake` and
  `checklist` feature slugs are dropped.
- R2. The multi-document packet parse path (the AI Wizard's main flow,
  `_parse_document_packet_now` in `ai.py`) is NOT scoped today and was
  missing from the call-site table. It is likely the single biggest token
  spender; added explicitly.
- R3. Help Center "Ask" runs on the anonymous public router
  (`public_help.py:219`), so request-default attribution cannot apply there;
  it gets a feature-only scope with user/tenant intentionally NULL.
- R4. New rule D-7 fixes a double-count flaw: Textract appears both in AWS
  Cost Explorer (Layer 2) and in per-deal metering (Layer 1), and measured
  LLM spend appears in both layers once provider billing is connected. The
  blend now counts each dollar exactly once.
- R5. `/unit-economics` had the same flaw in miniature: `fixed_monthly_usd`
  now explicitly excludes the variable components (AI + Textract) that the
  worksheet already charges per deal.
- R6. New gap G-7: the existing `/platform/ai-usage` endpoint reads raw rows
  unpaginated and will silently truncate at the PostgREST max-rows cap as
  volume grows; new endpoints aggregate SQL-side and the existing endpoint
  gets the same fix.
- R7. Cost-sync trigger hardened: "run at the 06:00 tick" became "run on any
  hourly tick when the last successful sync is older than 20 hours", so one
  failed tick no longer loses a day. Concurrent syncs coalesce.
- R8. Exact billing fee field confirmed: `deal_fee_cents` in
  `CreditSettingsResponse` (`app/schemas/credit.py:177`).
- R9. Cost Explorer is a global API served from us-east-1; the boto3 client
  must be created with that region regardless of `aws_region`.
- R10. The Users tab now lists every user (zero-usage included) via a LEFT
  JOIN from `users`, not just users who happen to have events.

---

## 0. Goal, scope, and non-goals

### 0.1 Goal

Give the platform admin (Jake, and Jan as operator) one professional-grade
console that answers, from real measured data:

1. What does each individual user cost us, in real time (OpenAI and Claude
   token usage, document OCR, and their share of everything else)?
2. What does the whole operation cost per day and per month across every
   service we pay for (AWS, Supabase, OpenAI, Anthropic, SendGrid, DocuSign,
   Google Cloud, domains)?
3. Given those measured costs and the revenue we already collect through the
   flat-fee wallet billing, what price per transaction is safe? The console
   must make the pricing decision easy, not make the decision itself.

### 0.2 Scope

- Backend: extend the existing AI usage metering with per-user attribution,
  add external service cost ingestion (AWS Cost Explorer verified working,
  Supabase Management API, provider billing APIs, manual registry), and add
  platform-admin-only aggregation endpoints.
- Frontend: one new page in the existing Platform sidebar group,
  `/platform/costs`, with four tabs (Overview, Users, Services, Pricing
  worksheet), built entirely from the project's existing platform design
  language and chart primitives.
- A frontend-only testing script that a real-estate professional can execute
  with a mouse and almost no typing.

### 0.3 Non-goals (hard guardrails)

- No billing behavior changes. This console is measurement and planning only.
  The wallet engine, flat fee, Stripe flows, and checkout are untouched
  (PAYMENT_BILLING_FLAT_FEE_UPDATE_PLAN.md remains the billing authority).
- No automatic model or provider switching. The admin-selected AI provider is
  used strictly as configured; this console only reports what it spends.
- No demo/sample data anywhere on the new surfaces. Honest empty states with
  instructions for generating real usage.
- No Recharts or any chart library. All charts are React SVG/CSS ports in the
  established project style.
- No new top-level navigation clutter: exactly one new item in the existing
  Platform sidebar group.

---

## 1. Verified current state (what already exists in source)

This section is the foundation the plan builds on. File references are exact.

### 1.1 AI usage metering already exists and is well designed

- Table `ai_usage_events`
  (`velvet-elves-backend/supabase/migrations/20260822090000_ai_usage_events.sql`):
  one row per AI provider call with `tenant_id`, `transaction_id`, `feature`,
  `provider`, `model`, `prompt_tokens`, `completion_tokens`, `cost_usd`
  (frozen at write time), `created_at`. RLS enabled, closed to anon clients.
- Recording happens at the provider boundary, so every OpenAI and Anthropic
  call is metered no matter which service triggered it:
  `app/services/providers/openai_provider.py:139,270` and
  `app/services/providers/anthropic_provider.py:137,261` both call
  `record_ai_usage(...)`.
- Attribution uses a `contextvars` scope (`app/services/ai_usage.py`,
  `ai_usage_scope(tenant_id=..., transaction_id=..., feature=...)`). Recording
  is best-effort and never raises into the AI path.
- Cost is computed at write time from a code-side rate table
  (`app/services/ai_usage.py:72-88`, USD per 1M tokens, longest-prefix match,
  `_DEFAULT_RATE = (3.0, 15.0)` fallback).
- Read side: `GET /platform/ai-usage`
  (`app/api/v1/platform_ai_usage.py`) aggregates by day / tenant /
  transaction / feature / provider / model, resolves tenant names and
  decrypts deal addresses for labels, and is gated by
  `require_platform_admin`.
- Frontend: `src/pages/platform/PlatformAIUsagePage.tsx` is a complete
  dashboard already in the target style: KPI tiles with sparklines, a
  switchable cost/calls/tokens trend, feature and provider donuts, ranked
  tenant/model bars, and a searchable per-deal table with CSV export.

### 1.2 Permission model already exists

- Backend: `require_platform_admin` dependency
  (`app/core/auth.py:240-255`) checks `users.is_platform_admin`, a
  vendor-side superuser flag deliberately orthogonal to the tenant-scoped
  `UserRole.ADMIN`. All new endpoints in this plan sit behind it.
- Frontend: `PlatformAdminGuard`
  (`src/components/platform/PlatformAdminGuard.tsx`) wraps the platform route
  subtree in `App.tsx:879-895` and renders a 404 for non-platform users, so
  the routes do not even exist for them.
- Navigation: the Platform sidebar group is appended at render time only when
  `user.is_platform_admin` is true (`src/layouts/AppLayout.tsx:343-348` and
  `447-464`), with defense-in-depth re-checking inside `buildSection`.
  Current items: Tenants, AI usage, Help center.

### 1.3 Scheduling infrastructure already exists

- `POST /internal/schedules/tick` (`app/api/v1/internal_schedules.py`) is a
  machine-callable fan-out endpoint, called hourly by EventBridge in prod and
  by `scripts/run_schedules.py` in dev, authenticated with
  `require_cron_secret` (header `X-VE-Cron-Secret`, fail-closed). This is the
  natural home for a daily cost-sync job.

### 1.4 Deployment and environment facts (verified on this machine)

- AWS account `388482955098`, IAM user `crazyaidev`
  (`aws sts get-caller-identity` succeeded).
- Cost Explorer access CONFIRMED WORKING: I ran
  `aws ce get-cost-and-usage` for June 2026 grouped by SERVICE and got real
  results. This removes the biggest feasibility risk for AWS cost data.
- AWS CLI v2.34.62 installed. Supabase CLI available via `npx supabase`
  (v2.109.0); it is not on PATH directly.
- AWS surface per AWS_ECS_CLOUDFRONT_PRODUCTION_DEPLOYMENT_PLAN.md and
  `app/core/config.py:138-157`: ECS Fargate backend, ALB, CloudFront + S3
  frontend, ECR, CloudWatch, Secrets Manager, NAT, Textract with an S3 input
  bucket (`textract_s3_bucket`), region default `us-east-2`.
- Paid third-party services visible in backend `.env` keys: Supabase, OpenAI,
  Anthropic, SendGrid, DocuSign, Stripe, Google (Pub/Sub, OAuth), Microsoft
  Graph. DNS is on GoDaddy (Route 53 hosting is a future item).
- Configured models right now: `OPENAI_MODEL="gpt-5.4"`,
  `ANTHROPIC_MODEL="claude-sonnet-4-6"`, `AI_PROVIDER=openai` in dev.
- Revenue-side tables that already exist for the pricing worksheet:
  `credit_wallets`, `credit_packs`, `credit_purchases`, `credit_ledger`
  (migration `20260824090000_credit_wallet.sql`), plus the flat-fee billing
  settings served by `GET /platform/billing/settings`
  (`app/api/v1/platform_billing.py:72`; the per-deal fee field is
  `deal_fee_cents` in `CreditSettingsResponse`, `app/schemas/credit.py:177`).
- Latest migration on disk is `20260908090000_flat_deal_fee.sql`, so this
  plan's `20260910090000` timestamp is safely last.
- Textract responses already expose page counts:
  `app/services/textract_service.py:178` reads
  `DocumentMetadata.Pages`, so per-parse OCR metering needs no new AWS calls.

### 1.5 Verified gaps and defects this plan must fix

G-1. **No per-user attribution at all.** `ai_usage_events` has no `user_id`
     column and `AIUsageContext` has no user field. "Cost per user" is
     currently impossible. This is the core ask.

G-2. **Attribution coverage is one call site out of roughly a dozen.**
     `ai_usage_scope(...)` is set only in `app/api/v1/ai.py:541`, and only on
     the SINGLE-document `/ai/parse` path. The multi-document packet path
     (`_parse_document_packet_now`, `ai.py` ~line 915, feeding
     `run_packet_parsing_pipeline`) is the AI Wizard's main flow and almost
     certainly the biggest token spender, and it is NOT scoped: its rows land
     as `tenant_id=NULL, feature='other'`. Other grep-verified AI entry
     points that record unattributed rows today: `ai.py`
     (`/resolve-documents`, `/recommend-tasks`, `/suggest-task-approach`,
     `/refresh-next-steps`, `/search-public-source`, `/wizard-command`),
     `transactions.py:1959` (supplemental task suggestions),
     `transaction_agent.py` (agent chat), `dashboard.py:878,2941,3862`
     (client chat + next-step refresh), `document_templates.py:185`,
     `ai_email_engine.py` (via `ai_emails.py:248,418,619,941`,
     `notifications.py:458`, the inbound hook in `main.py:71`, and the
     scheduler sweep), `help_ask_service.py` (via the anonymous
     `public_help.py:219`), `document_priority_ai_notes.py`,
     `ai_next_step_cache.py`, `attorney_packet_extraction.py` (via
     `attorney.py:455`), `vendor_task_verifier.py` (via
     `vendor_workspace.py`). Verified NON-issues: `/ai/intake/classify` and
     `/ai/parse-checklist` are deterministic (no LLM call; the checklist
     endpoint's docstring says so explicitly), and `suggestion_engine.py`
     is deterministic by design, so none of them need instrumentation.

G-3. **The rate table does not know the active OpenAI model.** `gpt-5.4`
     matches no prefix in `_MODEL_RATES`, so every OpenAI call today is
     costed at the `_DEFAULT_RATE` of $3.00/$15.00 per 1M tokens, which is an
     Anthropic Sonnet price applied to an OpenAI model. All OpenAI history
     since the switch to gpt-5.4 is potentially misstated.
     (`claude-sonnet-4-6` does resolve, via the `claude-sonnet-4` prefix.)

G-4. **No infrastructure or third-party cost data in the product at all.**
     AWS, Supabase, SendGrid, DocuSign, Google Cloud and domain costs are
     invisible; nothing ingests them and no table can hold them.

G-5. **Textract spend is not metered per deal or per user**, even though the
     page counts are already parsed and OCR is a real per-document variable
     cost alongside LLM tokens.

G-6. **No revenue-versus-cost view.** Revenue (wallet debits, purchases) and
     cost (AI usage) live in different silos; nobody can see margin per deal
     or per tenant, which is the actual pricing question.

G-7. **The existing read endpoint silently truncates at scale.**
     `platform_ai_usage.py` fetches raw `ai_usage_events` rows with a single
     unpaginated `.execute()` and aggregates in Python. Hosted Supabase caps
     PostgREST responses (`db-max-rows`, commonly 1000), so once the table
     passes the cap the dashboard undercounts with no error. All new
     aggregation endpoints in this plan therefore aggregate SQL-side (RPC /
     group-by), and Phase C also converts the existing endpoint to the same
     mechanism. First implementation step: check the project's actual
     max-rows setting so the fix is sized correctly.

---

## 2. Architecture decisions

D-1. **One attribution pipeline, two cost layers.**
     - Layer 1 (real-time, per-user): usage events written at call time
       (`ai_usage_events`, extended). LLM tokens and Textract pages both land
       here, each row priced at write time. Read queries aggregate live, so a
       tester's AI action appears on the console within seconds.
     - Layer 2 (daily, platform-level): `service_cost_daily` snapshots
       ingested from external billing APIs (AWS Cost Explorer verified,
       Supabase, provider billing) plus amortized manual registry entries.
       External providers only publish daily-resolution costs, so "real time"
       for Layer 2 honestly means "as of the last sync, with a visible
       freshness stamp and a Sync now button".

D-2. **Costs are frozen at write time, never recomputed.** This is the
     existing project philosophy (rate-table comment in `ai_usage.py`) and it
     extends to snapshots: editing a rate or a registry entry never rewrites
     history.

D-3. **Attribution defaults come from the authenticated request, not from
     hand-editing every endpoint.** `get_current_user` (async dependency,
     runs in the same request task, so a contextvar set there is visible to
     the endpoint and propagates into any `asyncio.create_task` children)
     will set a request-scoped default `AIUsageContext(user_id, tenant_id)`.
     Explicit `ai_usage_scope(...)` calls at the feature call sites then only
     need to add `feature` and `transaction_id`. Known limits, handled
     explicitly in A-3: (a) endpoints that do not depend on
     `get_current_user` get no defaults, which is exactly the anonymous
     public Help ask (`public_help.py`) and the vendor-token surfaces
     (`vendor_workspace.py`), so those call sites set explicit scopes;
     (b) background jobs (scheduler ticks, inbound email hook, auto-draft
     sweeps) set an explicit tenant-only scope. This makes "unattributed" a
     bug you can see, not the default. Implementation caution: `ai_usage.py`
     must stay import-light (it only imports the supabase client today) so
     `app/core/auth.py` can import it without a cycle.

D-4. **Measured versus billed reconciliation.** Internal token metering is
     the per-user source of truth; provider billing APIs (Anthropic admin
     usage/cost report, OpenAI organization costs) are ingested into Layer 2
     so the Overview can show "measured $X vs billed $Y" and catch rate-table
     drift like G-3 automatically. Exact endpoint shapes get verified during
     Phase B (V-2); if an admin key is not available the tile simply shows
     "billed: not connected" and nothing else degrades.

D-5. **Feature flag.** Everything ships behind `ve_cost_console_v1`
     (settings pattern already used by `ve_multi_workspace_v1` and friends),
     default ON in dev, so Jan controls exposure without a revert.

D-6. **Placement.** The console is fleet-console analytics, so it belongs in
     the Platform sidebar group next to Tenants and AI usage (platform
     *configuration* like Billing/Advertising lives in the Settings hub per
     the existing AppLayout comment). The existing `/platform/ai-usage` page
     stays untouched as the deep AI drill-down; the new page links into it.

D-7. **Every dollar is counted exactly once in the blend (R4).** Three
     overlaps exist and each gets an explicit rule:
     - Textract: AWS Cost Explorer already includes Textract under the AWS
       source. The Layer 1 Textract rows (A-5) exist for per-user/per-deal
       attribution only and are EXCLUDED from the platform-total blend.
     - LLM spend: the blend uses Layer 1 measured LLM cost as the AI source.
       Provider-billed rows ingested for reconciliation (B-3) are NEVER
       added to the blend; they only feed the "measured vs billed" gauge.
     - Registry vs API: a registry entry whose service is also API-ingested
       (e.g. someone adds "AWS" manually) is a misconfiguration; the
       registry UI warns when a name collides with an automated source.
     Blend definition used everywhere (Overview totals, run rate, fixed
     costs): `AWS (CE) + Supabase + manual registry + AI LLM measured`.

---

## 3. Phase A - Data foundations (backend, one migration)

All schema work is one additive migration,
`supabase/migrations/20260910090000_platform_cost_console.sql` (timestamped
after the unapplied flat-fee migration `20260908090000`). Jan applies
migrations; nothing here assumes the DB was already touched.

### A-1. Extend `ai_usage_events` for per-user attribution and non-token units

```sql
ALTER TABLE public.ai_usage_events
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS quantity NUMERIC(14,4),   -- e.g. Textract pages
    ADD COLUMN IF NOT EXISTS unit TEXT;                -- 'tokens' | 'pages'
CREATE INDEX IF NOT EXISTS idx_ai_usage_events_user
    ON public.ai_usage_events(user_id);
```

Nullable and additive: existing rows stay valid, the recorder never drops a
row because attribution was missing (existing philosophy preserved).
Known and accepted: the existing `tenant_id` FK is ON DELETE CASCADE, so
deleting a tenant erases that tenant's usage history and shrinks historical
totals; that matches the tenant-deletion privacy flow and is not changed
here. The new `user_id` uses SET NULL so removing one user keeps the row
(it degrades to tenant-level attribution). Platform-level history in
`service_cost_daily` is tenant-independent and unaffected either way.

### A-2. Plumb `user_id` through the usage context

- `AIUsageContext` gains `user_id: str | None`.
- `ai_usage_scope(...)` gains a `user_id` keyword.
- `record_ai_usage(...)` writes `user_id`, `quantity`, `unit`
  (`unit='tokens'`, `quantity=prompt+completion` for LLM rows so all rows are
  self-describing).
- New helper `ai_usage_request_defaults(user)` called from
  `get_current_user` in `app/core/auth.py`: sets a default context with
  `user_id` and `tenant_id` for the request task (D-3). Explicit scopes
  layered inside a request merge onto the defaults instead of replacing them
  (a small `merge=True` behavior in `ai_usage_scope`).

### A-3. Instrument every AI feature call site with feature + transaction

Standardized feature slugs (free-text column, no migration needed):
`extraction`, `chat`, `email`, `guidance`, `wizard`, `tasks`, `templates`,
`help`, `attorney`, `vendor`, `briefing`, `ocr`, `other`.
(R1: `intake` and `checklist` dropped; both endpoints are deterministic and
never reach a provider. `suggestion_engine.py` is deterministic too, so this
table is the complete LLM surface.)

| Call site (verified by reading each) | Scope to add |
| --- | --- |
| `api/v1/ai.py /parse` (single doc; already scoped at :541) | `user_id` arrives via request defaults; keep `extraction` |
| `api/v1/ai.py` packet path `_parse_document_packet_now` -> `run_packet_parsing_pipeline` (R2, UN-scoped today, the Wizard's main flow) | `extraction`; tenant + user from defaults; transaction id usually does not exist yet at parse time, stays NULL by design |
| `api/v1/ai.py /resolve-documents` | `extraction`, transaction id |
| `api/v1/ai.py /recommend-tasks`, `/suggest-task-approach` | `tasks`, transaction id |
| `api/v1/ai.py /refresh-next-steps` + `services/ai_next_step_cache.py` (also refreshed from `dashboard.py:2941`) | `guidance`, transaction id |
| `api/v1/ai.py /search-public-source` | `guidance` |
| `api/v1/ai.py /wizard-command` | `wizard` |
| `api/v1/transactions.py:1959` (supplemental task suggestions) | `tasks`, transaction id |
| `api/v1/transaction_agent.py` (agent threads) | `chat`, transaction id |
| `api/v1/dashboard.py:878` and `:3862` (chat replies) | `chat` |
| `api/v1/document_templates.py:185` (LLM) + `:81` (Textract field OCR) | `templates`; no transaction (template upload is tenant-level) |
| `services/ai_email_engine.py`, user-triggered via `ai_emails.py:248,418,619,941` + `notifications.py:458` | `email` + transaction id; user via request defaults |
| `services/ai_email_engine.py`, background via inbound hook (`main.py:71`) and scheduler auto-draft sweep | `email`, explicit tenant-only scope (no user exists) |
| `services/help_ask_service.py` via anonymous `public_help.py:219` (R3) | explicit `help` scope only; user and tenant intentionally NULL (public surface, `get_current_user` never runs) |
| `services/document_priority_ai_notes.py` (used from `dashboard.py`) | `briefing`, transaction id |
| `services/attorney_packet_extraction.py` via `attorney.py:455` | `attorney`, transaction id |
| `services/vendor_task_verifier.py` via `vendor_workspace.py` (vendor-token auth, not `get_current_user`) | explicit `vendor` scope with tenant + transaction id set from the vendor context |

Acceptance for A-3: run one action per feature in dev, then confirm zero new
rows with `feature='other'`, and `user_id IS NULL` only for the three paths
where that is by design (background email, public help, vendor tokens).
The check is a simple SQL query that also becomes a pytest.

### A-4. Fix the rate table and make drift visible (G-3)

- At implementation time, verify the current official price sheets for every
  model id in use (`gpt-5.4`, `claude-sonnet-4-6`, plus whatever
  `OPENAI_MODEL`/`ANTHROPIC_MODEL` are set to in stage/prod) and add explicit
  prefixes to `_MODEL_RATES`. Do not trust this plan's numbers; rates change.
- Add a startup log line when a configured model id resolves only to
  `_DEFAULT_RATE`, so the next model switch cannot silently repeat G-3.
- Do NOT rewrite historical rows (D-2). The Overview reconciliation tile
  (D-4) is the mechanism that exposes past misstatement.

### A-5. Meter Textract per parse (G-5)

In `textract_service.py`, after a job completes and `page_count` is parsed
(line 178), call `record_ai_usage(provider='aws-textract',
model='detect-document-text', prompt_tokens=0, completion_tokens=0,
quantity=page_count, unit='pages')` with cost from a new `_OCR_RATES` entry
(USD per 1,000 pages, verified against the AWS Textract price sheet at
implementation time; detect-text and analyze tiers differ).

Attribution accuracy note (corrects the Rev 1 claim that it was free
everywhere): the recorder inherits whatever scope is active at call time, so
coverage depends on A-3. Verified Textract call paths and their scopes:

- Single-doc `/ai/parse` -> `run_parsing_pipeline` -> Textract: already
  inside the `extraction` scope today; correct as-is.
- Packet path (`run_packet_parsing_pipeline`, Wizard): scoped only after the
  A-3 R2 fix; until then its pages would land unattributed.
- `document_templates.py:81` (template field OCR): scoped by A-3's
  `templates` row.
- `documents.py:646` only reads stored Textract geometry; it makes no
  Textract calls and needs nothing.

Per D-7 these rows are attribution detail (cost per deal / per user) and are
excluded from the platform-total blend, because AWS Cost Explorer already
bills Textract inside the AWS source.

### A-6. New tables for Layer 2

```sql
CREATE TABLE IF NOT EXISTS public.service_cost_daily (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source      TEXT NOT NULL,        -- 'aws' | 'supabase' | 'openai' | 'anthropic' | 'manual'
    service     TEXT NOT NULL,        -- e.g. 'Amazon ECS', 'AmazonCloudWatch', 'Supabase Pro plan'
    day         DATE NOT NULL,
    cost_usd    NUMERIC(12,4) NOT NULL DEFAULT 0,
    is_estimate BOOLEAN NOT NULL DEFAULT FALSE,  -- true for price-table computed / amortized rows
    meta        JSONB,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source, service, day)
);

CREATE TABLE IF NOT EXISTS public.service_cost_entries (   -- manual registry
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name           TEXT NOT NULL,          -- 'SendGrid Essentials', 'DocuSign', 'velvetelves.com domain'
    source         TEXT NOT NULL DEFAULT 'manual',
    monthly_usd    NUMERIC(12,2) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to   DATE,                   -- null = ongoing
    notes          TEXT,
    created_by     UUID REFERENCES public.users(id) ON DELETE SET NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Both RLS-enabled and closed to anon; only the service-role API layer reads
them, same posture as `ai_usage_events`. Registry entries are amortized to
days (`monthly_usd * 12 / 365.25`) by the aggregation layer at read time and
marked `is_estimate` in blended outputs.

---

## 4. Phase B - External cost ingestion

New module folder `app/services/cost_sources/` with one adapter per source
and a shared `cost_sync_service.py` orchestrator. Every adapter is
best-effort and isolated: one source failing must never block the others,
and each records its own `last_synced_at` + error into `platform_settings`
style state (visible in the UI as freshness stamps).

### B-1. AWS adapter (verified feasible)

- boto3 `ce.get_cost_and_usage`, `Granularity=DAILY`,
  `Metrics=['UnblendedCost']`, `GroupBy=[{'Type':'DIMENSION','Key':'SERVICE'}]`,
  window = last 45 days, upserted into `service_cost_daily` on
  `(source='aws', service, day)`. The 45-day re-pull matters because Cost
  Explorer restates recent days as usage settles.
- Cost Explorer is a global API served from us-east-1 (R9): create the
  client with `boto3.client('ce', region_name='us-east-1')` regardless of
  the app's `aws_region` (us-east-2). Handle `NextPageToken` pagination; a
  45-day grouped pull is typically 1-3 requests.
- IAM: add `ce:GetCostAndUsage` to the ECS task role and to the dev user.
  Cost Explorer is account-scoped, so this is one policy statement; note it
  in the deploy checklist. The CE API costs $0.01 per request; a daily sync
  of 1-3 requests is under $1/month, negligible but worth stating.
- boto3 is already a backend dependency (Textract), so no new package.

### B-2. Supabase adapter (probe first, honest fallback)

Supabase does not expose a stable public per-day cost API the way AWS does,
so this adapter is two-stage:

- V-1 probe (first implementation step): create a Supabase personal access
  token, then probe with it: `npx supabase projects list`,
  `GET https://api.supabase.com/v1/projects`, and the current
  organization/project usage and billing endpoints available on our plan.
  Whatever usage metrics are retrievable (DB size, storage size, egress,
  MAU) get ingested into `service_cost_daily.meta` and shown as usage meters.
- Cost rows: plan subscription fee entered once in the manual registry
  (amortized daily, `is_estimate=true`) plus computed overage estimates from
  the probed usage metrics against a code-side Supabase price table (same
  frozen-at-write philosophy). If the probe finds a real billing endpoint,
  it replaces the estimate; the UI treats both identically and labels
  estimates as such.

### B-3. Provider billing adapters (reconciliation, D-4)

- Anthropic: admin usage/cost report API with a new `ANTHROPIC_ADMIN_API_KEY`.
- OpenAI: organization costs/usage API with a new `OPENAI_ADMIN_API_KEY`.
- Both write `service_cost_daily` rows (`source='anthropic' | 'openai'`),
  powering the "measured vs billed" gauge. Optional: if keys are not
  provisioned, the adapters no-op and the gauge shows "not connected".
- Exact endpoint paths and response shapes verified at implementation (V-2);
  both APIs exist but have changed shape before.

### B-4. Manual registry (everything without an API)

SendGrid, DocuSign, Google Cloud (Pub/Sub is near-zero but real), GoDaddy
domains, and anything else get manual entries via the UI (Section 6, Services
tab). This is deliberate: a fixed monthly figure entered once beats a broken
scraper, and the client-facing question ("what does the whole operation
cost?") tolerates month-granularity for flat contracts.

### B-5. Scheduling and on-demand sync

- Extend the existing tick (R7, self-healing): on EVERY hourly tick,
  `internal_schedules.py` runs `cost_sync_service.sync_all()` if and only if
  the last successful sync is older than 20 hours (state kept in the same
  platform-settings style store as the freshness stamps). A failed 06:00
  attempt therefore retries on the next hour instead of losing the day. The
  tick response gains `cost_sync: {ran, aws: n_rows, supabase: ...,
  errors: [...]}` for observability, matching the existing response style.
- `POST /platform/costs/sync` (require_platform_admin) triggers the same
  `sync_all()` on demand and returns per-source outcomes. This powers the UI
  "Sync now" button so testers never wait for a schedule.
- Concurrency (R7): syncs coalesce behind a simple in-process lock; a sync
  requested while one is running waits for and returns the running sync's
  result instead of double-hitting the CE API. (Two ECS tasks could still
  sync simultaneously; the upsert on `(source, service, day)` makes that
  harmless, just slightly wasteful, which is acceptable.)
- Dev: `scripts/run_schedules.py` already exercises the tick; document
  `--cost-sync` usage in the script header.

### B-6. New secrets / env keys

`SUPABASE_MGMT_ACCESS_TOKEN`, `SUPABASE_PROJECT_REF` (dev/stage/prod refs),
`OPENAI_ADMIN_API_KEY` (optional), `ANTHROPIC_ADMIN_API_KEY` (optional).
Added to `.env.example` with comments, to Secrets Manager via the existing
`scripts/sync-env-to-aws-secret.ps1` flow, and to `app/core/config.py`
settings. Remember the memory rule: dev uvicorn does not hot-reload `.env`;
restart the backend after adding keys.

---

## 5. Phase C - Aggregation API (`app/api/v1/platform_costs.py`)

New router, prefix `/platform/costs`, every route gated by
`require_platform_admin`, registered in `router.py`, OFF behind
`ve_cost_console_v1`. All read endpoints accept `since`/`until` like the
existing AI usage endpoint.

| Endpoint | Purpose / response shape |
| --- | --- |
| `GET /platform/costs/overview` | Totals for the window using the D-7 blend (`AWS + Supabase + manual + AI LLM measured`; Layer 1 Textract rows and provider-billed rows excluded): `total_usd`, `mtd_usd`, `run_rate_month_usd` (mtd / elapsed days * days in month, labeled as run-rate), `by_source[]` (sources exactly: `aws`, `supabase`, `manual`, `ai_measured`), `by_service[]` (top-N), `by_day[]` (stacked by source), `ai_measured_vs_billed {measured_usd, billed_usd?, delta_pct?}` (reconciliation only, never in the blend), `freshness[] {source, last_synced_at, ok, error?}` |
| `GET /platform/costs/users` | The per-user table: `users` LEFT JOIN aggregated `ai_usage_events` (R10), so every user appears including zero-usage ones (service-role read, cross-tenant by design): per user `user_id, name, email, tenant_id, tenant_name, role, call_count, prompt_tokens, completion_tokens, ocr_pages, cost_usd, deal_count, cost_per_deal, last_activity_at, by_day_spark[]` (spark computed only for the returned page). Server-side `sort` (default cost desc) + `q` (name/email/tenant substring) + pagination |
| `GET /platform/costs/users/{user_id}` | Drill-down for the modal: totals, `by_feature[]`, `by_model[]`, `by_provider[]`, `by_day[]`, `by_transaction[]` (labels decrypted exactly like `platform_ai_usage.py:_safe_address`), plus tenant billing context: tenant plan, wallet balance, window debits from `credit_ledger` (revenue vs this user's cost) |
| `GET /platform/costs/services` | Layer-2 detail: `aws {by_service[], by_day[]}`, `supabase {usage_meters[], by_day[]}`, `providers {by_day[]}`, `registry_amortized[]` |
| `GET/POST /platform/costs/registry`, `PUT/DELETE /platform/costs/registry/{id}` | Manual cost entry CRUD. Server validates dates and positive amounts; deletes require the standard confirm flow client-side |
| `POST /platform/costs/sync` | On-demand sync (B-5), returns per-source results |
| `GET /platform/costs/unit-economics` | The pricing worksheet inputs, all measured: `avg_ai_cost_per_deal` + `median_ai_cost_per_deal` (LLM rows per transaction), `avg_ocr_cost_per_deal` (Textract rows per transaction), `deals_in_window`, `active_users` (users with at least one event in window), `fixed_monthly_usd` computed per R5 as the D-7 blend MINUS the variable components the worksheet already charges per deal (minus `ai_measured`, minus the AWS "Amazon Textract" service line), `current_fee_usd` (= `deal_fee_cents / 100` from the billing settings, R8), `revenue_cash_window_usd` (completed `credit_purchases`, money actually collected) and `revenue_consumed_window_usd` (`credit_ledger` fee debits, fees earned by usage); the worksheet labels the two revenue figures distinctly |

Implementation notes:

- Aggregation happens SQL-side (Postgres RPC / group-by), never by fetching
  raw rows into Python: that is the G-7 truncation lesson. Phase C also
  converts the existing `/platform/ai-usage` handler to the same RPC so the
  two surfaces cannot drift apart as volume grows. `ai_usage_events` already
  has the right indexes and gains `idx_ai_usage_events_user` in A-1.
- Money is returned as numbers, 6-decimal rounded like the existing endpoint;
  formatting stays client-side (`money()` helper already exists).
- Unlabeled rows (null user/tenant from background jobs) are never dropped:
  they surface as an explicit "Background / unattributed" row so totals always
  reconcile with the AI usage page.

---

## 6. Phase D/E - Frontend: the Costs & pricing console

### 6.1 Placement and shell

- Route `ROUTES.PLATFORM_COSTS = '/platform/costs'` in
  `src/utils/constants.ts`, registered inside the existing
  `PlatformAdminGuard` subtree in `App.tsx`.
- Sidebar: one item appended to the Platform group in `AppLayout.tsx`:
  `{ to: ROUTES.PLATFORM_COSTS, icon: CircleDollarSign, iconColor: 'text-ve-green', label: 'Costs & pricing' }`
  (lucide icon per the no-emoji rule).
- Page skeleton copies the proven pattern from `PlatformAIUsagePage.tsx`:
  `PlatformPageHeader` (title "Costs & pricing", badge = month-to-date total
  in the mono tabular-nums pill style, trailing = time-range
  `SegmentedControl`: 7 / 30 / 90 days / All time), then
  `flex h-full min-h-0 flex-col overflow-hidden` with an inner
  `flex-1 overflow-y-auto` scroll area (pages own their scroll).
- Tabs via `SegmentedControl` directly under the header, synced to a
  `?tab=` search param so the testing guide can deep-link:
  **Overview | Users | Services | Pricing**.
- Style: flat modern tool aesthetic (no gradient strips, hairline
  `ve-border` dividers, sentence-case labels), `ve-*` tokens only, light mode
  only, all numbers `font-mono tabular-nums`. Charts reuse the existing SVG
  primitives (`CostTrendChart`, `CostDonut`, `RankedBars` from
  `AiUsageCharts.tsx`; `ChartCard`, `KpiCard` from `AnalyticsCharts.tsx`).
  Two new primitives, built as SVG ports in the same file style:
  `StackedTrendChart` (daily cost stacked by source) and `UsageMeter`
  (Supabase quota bars).

### 6.2 Tab 1: Overview (the "what does everything cost" answer)

- KPI row (4 `KpiCard`s with real sparklines): Month-to-date total / Daily
  run rate + projected month (labeled "run-rate estimate") / AI cost
  (measured) / Infrastructure & services.
- Flagship `StackedTrendChart`: daily cost stacked by the four D-7 blend
  sources (AWS, Supabase, AI measured, Manual), with a metric toggle
  Total / By source. Textract shows up inside the AWS band here (it is an
  AWS bill line); its per-deal attribution lives on the Users tab. This
  keeps the flagship chart's total equal to real money spent, once.
- Two `ChartCard`s side by side: donut "Cost by source" and ranked bars
  "Top services" (Amazon ECS, Textract, CloudFront, Supabase plan, ...).
- Reconciliation strip: "AI measured $X · billed $Y · delta Z%" with a plain
  sentence explaining what a drift means; shows "billed: not connected" when
  admin keys are absent.
- Freshness footer: one line per source, "AWS synced 2h ago", with a
  `Sync now` button (calls `POST /platform/costs/sync`, spinner, then
  refetch). Estimates are marked with a small "est." neutral chip.
- Empty state (no synced data yet): honest copy telling the admin to press
  Sync now or add registry entries, no fake numbers.

### 6.3 Tab 2: Users (the per-user real-time ask)

- Controls row directly above the list (list-page rule: no intro prose):
  search input left (name / email / tenant), right-aligned h-9 controls:
  sort `SegmentedControl` (Cost | Calls | Recent) and a CSV export button
  (blob + forced `<a download>`, the established pattern).
- Table (mirrors the `/admin/users` table anatomy): User (name + email),
  Tenant, Role chip, AI calls, Tokens (in · out), OCR pages, Cost,
  Cost / deal, 14-day sparkline, Last activity. Every user appears, zero
  usage included (R10), so "who is NOT costing anything" is answerable too;
  zero rows render ghost-text dashes, not fake zeros with sparklines.
  Totals row in `tfoot`. A pinned "Background / unattributed" row (plus a
  "Public help center" line when the anonymous Ask feature has spend) keeps
  totals honest.
- Row click opens a **detail modal** (Jan's rule: directories are tables,
  detail is a modal, shadcn `Dialog`; `DialogContent` brings its own close
  button, do not add another): identity header, KPI row for the window,
  feature donut, daily trend, per-deal table with the same search + CSV as
  the AI usage page, model/provider split, and a billing-context footer
  (tenant plan, wallet balance, window revenue vs this user's cost).
- Real-time definition made visible: a caption "Live: aggregated from AI
  events at load time" plus a refresh button; a tester can run a wizard
  parse in another tab and see their own row move.

### 6.4 Tab 3: Services (AWS + Supabase + registry)

- AWS section: ranked bars by service for the window, daily trend, and a
  small month-over-month compare (this month vs last, per service, with
  green/red deltas using the status triads).
- Supabase section: plan card (from registry) + `UsageMeter` rows for the
  probed metrics (DB size, storage, egress, MAU) with plan limits, plus
  estimated overage cost when applicable, clearly marked "est.".
- Managed services registry: table of manual entries (name, monthly cost,
  effective range, notes) with Add / Edit via a small modal: preset service
  name suggestions (SendGrid, DocuSign, Google Cloud, Domains) so entry is
  two clicks and one number; Delete goes through `useConfirm` (destructive
  action rule). Per D-7, saving a name that collides with an automated
  source (e.g. "AWS") shows an inline warning that this cost is already
  ingested automatically. This is the only data entry in the whole console,
  by design.

### 6.5 Tab 4: Pricing (the worksheet that answers the actual question)

Read-only measured inputs on the left, one adjustable scenario on the right,
zero required typing (sliders + steppers with sensible ranges):

- Measured (auto-filled from `/unit-economics`, each with an info tooltip
  explaining its source): average and median AI+OCR cost per deal, fixed
  monthly cost (blend minus per-deal variables, R5, so nothing is charged
  twice), deals per month in window, active users, current per-transaction
  fee (`deal_fee_cents / 100`), and both revenue figures side by side: cash
  collected (purchases) and fees consumed (ledger debits), labeled so the
  difference (prepaid, unconsumed balance) is understandable.
- Scenario controls: candidate fee per transaction (stepper, defaults to the
  current fee), projected deals per month (slider, defaults to measured).
- Outputs, written as plain sentences with the numbers highlighted:
  margin per deal (fee minus variable cost), projected monthly profit
  (deals x fee minus deals x variable minus fixed), break-even deals per
  month (fixed / (fee minus variable)), and a small sensitivity table for
  fee-10%, fee, fee+10%. When the candidate fee does not cover the variable
  cost per deal, the worksheet says so plainly ("this fee loses money on
  every deal") instead of rendering a negative break-even.
- Guardrail copy at the top: "This worksheet models a price; it does not
  change billing." Nothing on this tab writes anywhere.

### 6.6 Frontend data layer

`src/hooks/usePlatformCosts.ts` following `usePlatformTenants.ts` patterns:
`useCostOverview(range)`, `useCostUsers(params)`, `useCostUserDetail(id)`,
`useCostServices(range)`, registry mutations with query invalidation, and
`useCostSync()`. All via the existing `useApiFetch`/`useApiMutate` helpers.

---

## 7. Permissions (explicit, testable)

- Backend: every `/platform/costs/*` route depends on
  `require_platform_admin`; the sync tick path uses `require_cron_secret`.
  No tenant-scoped role, including tenant Admin, can reach any of it (the
  guard's existing anti-enumeration rationale applies verbatim).
- Frontend: route lives inside `PlatformAdminGuard` (404 for others), nav
  item renders only for `is_platform_admin`, and `buildSection('platform')`
  keeps its defense-in-depth re-check.
- Tests: pytest for 403 on a tenant-admin token and 200 on a platform-admin
  token for each new endpoint; the tester script covers the UI side
  (Section 9, steps N-1/N-2).

---

## 8. Phase sequencing, estimates, acceptance criteria

| Phase | Content | Est. | Acceptance |
| --- | --- | --- | --- |
| A | Migration + user attribution + call-site scopes (incl. the Wizard packet path, R2) + rate-table fix + Textract metering | 2-2.5 d | One action per feature in dev produces a correctly attributed row (user, tenant, feature, transaction); a Wizard packet parse is attributed; zero `feature='other'` anywhere; `user_id IS NULL` only on the three by-design paths (background email, public help, vendor tokens); startup warns on unknown model ids; Textract parse writes a `pages` row |
| B | Cost sources: AWS adapter, V-1 Supabase probe + adapter, registry, sync orchestrator + tick + on-demand sync, secrets | 2-3 d | `POST /platform/costs/sync` fills `service_cost_daily` with real June/July AWS numbers; per-source freshness recorded; one failing source does not block others; a second sync while one runs coalesces instead of double-calling CE |
| C | Aggregation endpoints (SQL-side per G-7) + converting `/platform/ai-usage` to the same RPC + pytest coverage | 2-2.5 d | All endpoints return correct shapes against seeded events; 403/200 permission tests pass; totals reconcile with `/platform/ai-usage` for the same window; blend total counts Textract and provider bills exactly once (D-7 test with overlapping seeded data) |
| D | UI: shell + Overview + Users (+ detail modal) | 2.5-3 d | Screenshot pass; live-update demo (run a parse, see the user row change) |
| E | UI: Services + registry CRUD + Pricing worksheet | 2-2.5 d | Screenshot pass; registry add/edit/delete with confirm; worksheet math spot-checked against hand calculation |
| F | Testing guide file + full click-through + screenshot set for Jake | 0.5-1 d | Section 9 script executes end to end with zero developer intervention |

Total: roughly 11-14.5 dev days. Order is strict A -> B -> C -> D -> E -> F;
D can start once C's overview/users endpoints exist even if B's Supabase
adapter is still in probe.

Verification method per project memory: never ship UI blind; render with the
fresh dev backend on :8001 + frontend :5173, screenshot via headless Chrome,
and compare against the platform pages for style fidelity before calling any
phase done.

---

## 9. Frontend-only validation script (for real-estate professional testers)

Preconditions Jan sets up once: a platform-admin login and a normal
tenant-admin login on the dev stack, backend restarted after the new env
keys, migration applied.

Positive path (mouse only, typing limited to a search word and one number):

1. Sign in as the platform admin. Confirm the left sidebar shows the
   Platform group with the new "Costs & pricing" item.
2. Open it. The Overview tab loads with either real tiles or an honest empty
   state that tells you to press "Sync now".
3. Press "Sync now". Watch the freshness footer update and the AWS tiles
   fill with real dollar amounts. (Expected: numbers match the AWS console's
   Cost Explorer for the same days; Jan verifies once, testers just confirm
   numbers appear.)
4. Switch the range control 7 / 30 / 90 / All and confirm every chart
   redraws without errors.
5. Open the Users tab. Confirm you can see yourself and other users with
   cost columns. Type part of a user's name in search; the table filters.
6. In another browser tab, run any AI action (e.g. upload a contract through
   the wizard, or ask the AI chat a question). Return, press refresh on the
   Users tab, and confirm that user's calls/cost increased. This is the
   real-time check.
7. Click the user's row. The detail modal opens: feature donut, daily trend,
   per-deal costs, billing context. Press CSV and confirm a file downloads.
8. Open the Services tab. Confirm AWS services are listed with costs.
   Press "Add service cost", pick "SendGrid" from the presets, enter a
   monthly amount, save. Confirm it appears in the registry table and, after
   a refresh, in the Overview blend. Edit it; delete it; confirm the delete
   asks for confirmation first.
9. Open the Pricing tab. Confirm the measured numbers are filled in. Move
   the fee stepper and the deals slider; confirm the margin, monthly profit,
   and break-even sentences update instantly and read sensibly.

Negative path:

- N-1. Sign in as the tenant admin (not platform admin). Confirm the
  Platform group is absent from the sidebar entirely.
- N-2. While signed in as the tenant admin, paste `/platform/costs` into the
  address bar. Confirm a 404 page, not an error and not data.

Deliverable of Phase F: this script, expanded with screenshots, saved as
`velvet-elves-data/PLATFORM_COST_CONSOLE_TESTING_GUIDE.md`.

---

## 10. Open items that need a human decision (not blockers to start)

J-1. Supabase Management API token: Jan creates it and confirms which usage
     endpoints our plan tier actually exposes (V-1). Until then Supabase
     shows plan fee + "usage metrics not connected".
J-2. OpenAI / Anthropic admin keys for the billed-cost reconciliation: nice
     to have, adapters no-op without them.
J-3. Should Stripe processing fees and future commission payouts
     (`ve_commission_payouts_v1`, currently parked) appear as cost lines?
     Proposal: yes eventually, via a Stripe balance-transaction adapter, but
     explicitly out of scope for v1 to keep the surface testable.
J-4. Pricing itself stays Jake's call; the worksheet defaults to the
     currently configured flat fee and never writes anything.

---

## 11. Compliance checklist against project rules

- Measurement only, no billing coupling; wallet/flat-fee system untouched.
- Additive migration only; Jan applies it; timestamped after `20260908090000`.
- AI provider selection untouched; no fallback or auto-switching introduced.
- Platform permission gates on every route, nav item, and guard, with tests.
- Tables + modals for directories, controls row over lists, no intro prose,
  flat tool aesthetic, `ve-*` tokens, lucide icons, light mode only.
- SVG chart ports only, KPI cards with sparklines, mono tabular-nums figures.
- Honest empty states, no demo data, no simulate buttons on real surfaces.
- Downloads use the blob + forced-save pattern.
- Every capability validated through the UI by non-developers (Section 9).
