# Velvet Elves - Help Center (Platform-Managed) Superior Build Plan

Date: 2026-06-25
Status: IMPLEMENTED (Phases H0-H2 + the H3 SEO prerender), 2026-06-25. The plan below is the spec; what shipped:
- H0 backend: migration `20260830090000_help_center.sql` (tables + RLS + `help-media` bucket + seeded settings), models/repos/services/schemas, authoring router `app/api/v1/platform_help.py` (require_platform_admin) + public router `app/api/v1/public_help.py` (flag-gated, published-only), registered in `router.py`, config flag `ve_help_center_v1`. Tests: `app/tests/test_help_center.py` (5 passing; full suite collects, 30 platform tests green).
- H1 admin UI (`velvet-elves-frontend`): routes/pages under `/platform/help/*` (collections table, per-collection articles, two-pane editor with toolbar + live preview + image upload, in-app preview, feedback, settings), hooks `useHelpCenter.ts`, shared `HelpArticleBody`, Platform-nav entry. tsc + lint clean.
- H2 separate site (`c:\Projects\velvet-elves-help-center`): Vite/React/Tailwind reusing `ve-*` tokens; Home/Collection/Article (TOC + related + feedback)/Search/NotFound; full GFM/slug/sanitize markdown; ChatWidget (Intercom/Crisp embed or contact panel); builds clean.
- H3: `scripts/prerender.mjs` (per-route meta + sitemap, degrades gracefully) + sample deploy workflow + **article revision history/restore UI** (`RevisionsModal` + editor "History" button).
- H4 ("Ask AI", now done): public `POST /public/help/ask` (`HelpAskService`, retrieval-first, grounds an answer in published articles via the configured AI provider when a real key exists, else returns retrieval citations — so it works locally with no keys) + the website's messenger `ChatWidget` rendering the answer with numbered source-citation chips. The `chat_provider` setting still switches to Intercom/Crisp embeds, so Jake's build-vs-embed choice (Q1) is preserved.
- Local testing: `HELP_CENTER_LOCAL_TESTING_GUIDE.md`, website `.env`, and `localhost:5180` added to the backend `cors_origins` default.
Everything builds/tests clean: backend `test_help_center.py` 6 passing; main frontend tsc + lint clean; help-center site builds. EXCLUDES deployment (per Jan: testing locally first). Uncommitted (Jan commits). For prod, add the help domains to `cors_origins` and flip `ve_help_center_v1` on.

Reference benchmark: `help.listedkit.com` (the nine screenshots in `listedkit_help_center_screenshots/`).
Grounding sources reviewed for this plan: `SYSTEM_DESIGN.md`, `STYLE_GUIDE.md`, `AWS_ECS_CLOUDFRONT_PRODUCTION_DEPLOYMENT_PLAN.md`, `milestones.txt`, and the live backend/frontend source (auth/RBAC, router registration, migrations, platform-admin pages, design tokens). Concrete file references are cited inline so implementation is turnkey.

---

## 0. The one-paragraph summary

I am building a public Help Center website as a **completely separate project** at `c:\Projects\velvet-elves-help-center`, whose entire content (categories, articles, media, support links, and reader feedback) is **authored and managed from inside the main Velvet Elves app by platform-admin users only**. The main app gains a new platform-admin authoring surface plus two backend API surfaces: a secured authoring API (`/api/v1/platform/help/...`, gated by `require_platform_admin`) and a public, unauthenticated, PII-free read API (`/api/v1/public/help/...`) that the separate website consumes. The separate website is a Vite/React/Tailwind static site that reuses the project's `ve-*` design tokens so it harmonizes with the product, and it deploys to `help.velvetelves.com` (S3 + CloudFront), a domain the AWS deployment plan already reserves. Every authoring action is mouse-first and fully testable through the UI by non-developer testers.

---

## 1. Objective and the governing constraint

### 1.1 Objective
Ship a production help center that matches the ListedKit reference: a searchable knowledge base of categorized articles, with per-article table-of-contents, related articles, reader feedback, a support/contact path, and an AI support widget, presented in a modern, premium interface that reads as a professional tool for real-estate experts.

### 1.2 Governing constraint (non-negotiable)
**All content shown on the help center website is managed within the main project, and only users with the `is_platform_admin` flag may manage it.** The separate website is a pure consumer of published content. It never writes content and never needs an authenticated session.

This maps cleanly onto patterns that already exist in the codebase:
- Platform-admin gating: `require_platform_admin` in `velvet-elves-backend/app/core/auth.py` and `PlatformAdminGuard` in `velvet-elves-frontend/src/components/platform/PlatformAdminGuard.tsx` (which renders a 404, not a 403, so the route tree does not leak).
- Public, unauthenticated, PII-free read endpoints: the established precedent is `velvet-elves-backend/app/api/v1/public_branding.py` (prefix `/public`, no auth dependency, returns only safe fields). The help read API follows the same shape.
- Operator-tunable config without code edits: `platform_settings` key-value table (migration `20260825090000_platform_settings.sql`), service-role RLS, platform-admin enforced in the API layer. The help center's support links and chat config live here.

---

## 2. Reference analysis (what the screenshots require)

I inventoried every screenshot and converted it into a concrete feature list. "All the features shown in the screenshots are necessary", so each item below is in scope.

### 2.1 Public home page (Screenshot_21, _22, _23)
- A dark navy gradient hero banner.
- Top bar: product logo (top-left), a "Book a Call" link and a language selector ("English" with a globe), top-right.
- Centered title: "ListedKit AI Help Center" (for us: a configurable site title).
- A large, prominent search box ("Search for articles...").
- A vertical list of **Collections** (categories), each rendered as a card with: a tinted rounded-square icon, a title, a one-line description, and an article count ("23 articles").
- Collections visible in the reference: Getting Started ("Credits, pricing, and transaction types", 23), Navigation & Dashboard ("Sidebar, settings, and dashboard features", 5), Contacts & Parties ("Adding, editing, and managing contacts", 4), Email ("Gmail setup, templates, auto-drafting, and scheduling", 13), Documents.
- A floating chat/support launcher (bottom-right).

### 2.2 Search results (Screenshot_52)
- The search box stays prominent; below it, a results list.
- Each result row shows the article title (as a question) plus a short answer snippet, and links into the article.

### 2.3 Article page (Screenshot_53, _54)
- The same dark hero/search header persists at the top.
- Breadcrumb: "All Collections > {Collection} > {Article title}".
- Large article title and a publish/updated date ("February 4, 2026").
- Rich body content: bold lead paragraph, section headings, bullet lists, inline emphasis, inline images.
- A right-hand **table of contents** built from the article's headings, with the active section highlighted as the reader scrolls.
- A "Related Articles" block: a list of links with right chevrons.
- A "Did this answer your question?" feedback widget with three emoji reactions (negative / neutral / positive).
- A dark footer with the site name and "Book a call" / "Email us" links.

### 2.4 AI support / live chat widget (Screenshot_23, _24, _25, _26)
- A messenger-style panel ("ListedKit Support") launched bottom-right.
- An AI agent answers natural-language questions with rich formatting (bold, numbered lists), **numbered source citations**, and inline image carousels.
- A follow-up prompt ("Is that what you were looking for?").
- A composer (attachment, emoji, GIF, mic) and an "Expand window" affordance.

### 2.5 Cross-cutting
- Multi-language support (the language selector implies localized content).
- A "Book a Call" CTA and an "Email us" support path throughout.

### 2.6 Resulting feature list
1. Collections (categories) with icon, title, description, ordering, article count.
2. Articles with title, slug, rich body, excerpt, date, ordering, status.
3. Per-article table of contents (derived from headings).
4. Related articles (curated, with same-collection fallback).
5. Full-text search with ranked title+snippet results.
6. Reader feedback (3-way reaction, optional comment).
7. Support links (Book a Call, Email us) and language selector.
8. AI support widget with citations (Phase 4), or an embedded third-party messenger as the simpler alternative.
9. A platform-admin authoring back office for all of the above, inside the main app.

---

## 3. System architecture

Three surfaces, one content store.

```
                         MAIN PROJECT (velvet-elves)
  ┌───────────────────────────────────────────────────────────────────┐
  │  Frontend: Platform-admin authoring UI  (/platform/help/*)          │
  │    PlatformAdminGuard + ve_help_center_v1 flag                      │
  │            │ JWT (platform admin)                                    │
  │            ▼                                                         │
  │  Backend authoring API   /api/v1/platform/help/*                    │
  │    Depends(require_platform_admin)                                  │
  │            │                                                         │
  │            ▼                                                         │
  │  Services → Repositories → Supabase (Postgres + Storage)            │
  │    help_collections · help_articles · help_article_feedback        │
  │    help_article_related · help_article_revisions · help-media bucket│
  │            ▲                                                         │
  │            │  (published-only, PII-free reads)                      │
  │  Backend public API      /api/v1/public/help/*    (NO AUTH)         │
  └────────────────────────────────▲──────────────────────────────────┘
                                    │ HTTPS (CORS: help domains)
                                    │
  ┌─────────────────────────────────┴─────────────────────────────────┐
  │   SEPARATE PROJECT: velvet-elves-help-center                        │
  │   Vite + React + Tailwind static site (reuses ve-* tokens)          │
  │   Pages: Home · Collection · Article · Search · (Ask AI widget)     │
  │   Deployed: S3 + CloudFront → help.velvetelves.com                  │
  └────────────────────────────────────────────────────────────────────┘
```

Why this split:
- The content lives in the main app's database and is governed by the same platform-admin identity, satisfying the governing constraint with zero new auth machinery.
- The public website never holds a session and never sees PII, so it can be a fully static, cacheable, separately deployed surface (exactly how the AWS plan already treats `help.velvetelves.com`).
- The authoring surface is just another platform-admin area, reusing `PlatformAdminGuard`, `PlatformPageHeader`, the Platform nav group, and the design system.

---

## 4. Data model (main project)

New tables, added as one raw-SQL migration in `velvet-elves-backend/supabase/migrations/`, following the exact house style of `20260825090000_platform_settings.sql`: `BEGIN; ... COMMIT;`, `ENABLE ROW LEVEL SECURITY`, a service-role-only RLS policy, and access enforced in the API layer (the backend uses the service-role client). Suggested filename: `20260830090000_help_center.sql`.

### 4.1 `help_collections` (categories)
```sql
CREATE TABLE IF NOT EXISTS public.help_collections (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug          TEXT NOT NULL,                 -- URL segment, unique per locale
  locale        TEXT NOT NULL DEFAULT 'en',
  name          TEXT NOT NULL,
  description   TEXT,                           -- one-line subtitle on the card
  icon          TEXT NOT NULL DEFAULT 'BookOpen', -- lucide-react icon name
  icon_tone     TEXT NOT NULL DEFAULT 'green',  -- tile tint key (matches reference green)
  sort_order    INTEGER NOT NULL DEFAULT 0,
  is_published  BOOLEAN NOT NULL DEFAULT FALSE,
  created_by    UUID REFERENCES public.users(id) ON DELETE SET NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (locale, slug)
);
```

### 4.2 `help_articles`
```sql
CREATE TABLE IF NOT EXISTS public.help_articles (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  collection_id       UUID NOT NULL REFERENCES public.help_collections(id) ON DELETE CASCADE,
  slug                TEXT NOT NULL,
  locale              TEXT NOT NULL DEFAULT 'en',
  translation_group   UUID NOT NULL DEFAULT gen_random_uuid(), -- links same article across locales
  title               TEXT NOT NULL,
  excerpt             TEXT,                  -- search snippet + related-list summary
  body_md             TEXT NOT NULL DEFAULT '', -- Markdown (GFM)
  status              TEXT NOT NULL DEFAULT 'draft', -- draft | published | archived
  sort_order          INTEGER NOT NULL DEFAULT 0,
  seo_title           TEXT,
  seo_description     TEXT,
  author_user_id      UUID REFERENCES public.users(id) ON DELETE SET NULL,
  published_at        TIMESTAMPTZ,           -- the date shown on the article
  view_count          INTEGER NOT NULL DEFAULT 0, -- updated by an opt-in beacon, NOT on every public GET (see 5.3)
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- ranked full-text search over title + excerpt + body
  search_tsv          tsvector GENERATED ALWAYS AS (
                        setweight(to_tsvector('english', coalesce(title,'')), 'A') ||
                        setweight(to_tsvector('english', coalesce(excerpt,'')), 'B') ||
                        setweight(to_tsvector('english', coalesce(body_md,'')), 'C')
                      ) STORED,
  UNIQUE (locale, slug)
);
CREATE INDEX IF NOT EXISTS idx_help_articles_collection ON public.help_articles (collection_id);
CREATE INDEX IF NOT EXISTS idx_help_articles_status ON public.help_articles (status);
CREATE INDEX IF NOT EXISTS idx_help_articles_search ON public.help_articles USING GIN (search_tsv);
```

Notes:
- The table-of-contents is derived from the headings in `body_md` at render time, so it needs no storage and never drifts from the body.
- `published_at` is set the first time an article is published and is the human-readable date shown on the public article.
- The slug is auto-derived from the title on first save, then frozen: editing the title later does NOT silently re-slug a published article (that would break live URLs and inbound links). Changing a published slug is a deliberate action (and should leave a redirect; see 5.2).
- Full-text search indexes `body_md` (raw Markdown). Markdown markers tokenize away cleanly enough, but the public snippet is built primarily from `excerpt` (weight B) for clean results. A later refinement can store a Markdown-stripped `body_text` shadow column to feed weight C and `ts_headline`; it is not required for launch.

### 4.3 `help_article_related` (curated related articles)
```sql
CREATE TABLE IF NOT EXISTS public.help_article_related (
  article_id   UUID NOT NULL REFERENCES public.help_articles(id) ON DELETE CASCADE,
  related_id   UUID NOT NULL REFERENCES public.help_articles(id) ON DELETE CASCADE,
  sort_order   INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (article_id, related_id),
  CHECK (article_id <> related_id)
);
```
When an article has no curated related rows, the public API falls back to other published articles in the same collection.

### 4.4 `help_article_feedback` (reader reactions)
```sql
CREATE TABLE IF NOT EXISTS public.help_article_feedback (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  article_id   UUID NOT NULL REFERENCES public.help_articles(id) ON DELETE CASCADE,
  rating       SMALLINT NOT NULL CHECK (rating IN (-1, 0, 1)), -- sad / neutral / happy
  comment      TEXT,                      -- optional, length-capped in the API
  locale       TEXT,
  path         TEXT,                      -- page the reader was on
  session_hash TEXT,                      -- hashed IP+UA, de-dupe + abuse control
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_help_feedback_article ON public.help_article_feedback (article_id);
```

### 4.5 `help_article_revisions` (Phase 3, versioning)
```sql
CREATE TABLE IF NOT EXISTS public.help_article_revisions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  article_id    UUID NOT NULL REFERENCES public.help_articles(id) ON DELETE CASCADE,
  title         TEXT NOT NULL,
  excerpt       TEXT,
  body_md       TEXT NOT NULL,
  edited_by     UUID REFERENCES public.users(id) ON DELETE SET NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 4.6 RLS (every table)
```sql
ALTER TABLE public.help_collections ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_help_collections ON public.help_collections;
CREATE POLICY service_role_help_collections ON public.help_collections
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');
-- repeat for help_articles, help_article_related, help_article_feedback, help_article_revisions
```
The backend already reaches Supabase through the service-role client, and platform-admin authorization is enforced in the API layer by `require_platform_admin`. This is the same posture as `platform_settings`. Public reads also go through the backend (the website calls the FastAPI public API, never Supabase directly), so RLS staying service-role-only is correct.

### 4.7 Storage bucket for article media
Create a public Supabase Storage bucket `help-media` **in the same migration**, mirroring the verified pattern in `supabase/migrations/20260506_logos_bucket.sql`: `INSERT INTO storage.buckets (... public=true, file_size_limit, allowed_mime_types image/*) ON CONFLICT (id) DO UPDATE`, plus a `service_role_help_media_all` policy (FOR ALL TO service_role) and a `public_read_help_media` policy (FOR SELECT TO public). Admins upload images by drag-drop in the editor; writes go only through the authoring API's service-role client; the returned public URL (`{SUPABASE_URL}/storage/v1/object/public/help-media/...`) is embedded into `body_md`. Creating the bucket in-migration (not by hand in the dashboard) keeps the deploy turnkey, exactly like the existing `logos` and `documents` buckets.

### 4.8 Help-center settings (no new table)
Support links and chat configuration reuse `platform_settings`. Seed keys (safe defaults) in the same migration:
```sql
INSERT INTO public.platform_settings (key, value) VALUES
  ('help_site_title',      'Velvet Elves Help Center'),
  ('help_book_a_call_url', ''),
  ('help_support_email',   ''),
  ('help_default_locale',  'en'),
  ('help_chat_provider',   'none'),   -- none | ask_ai | intercom | crisp
  ('help_chat_app_id',     '')
ON CONFLICT (key) DO NOTHING;
```

---

## 5. Backend (main project)

Layering follows `SYSTEM_DESIGN.md` 1.2 (Routers → Services → Repositories) and the existing platform-router conventions.

### 5.1 New files
- Models (plain dataclasses, like `app/models/document_template.py`): `app/models/help_collection.py`, `app/models/help_article.py`, `app/models/help_feedback.py`.
- Repositories: `app/repositories/help_repository.py` (collections + articles + related + revisions), `app/repositories/help_feedback_repository.py`.
- Services: `app/services/help_content_service.py` (CRUD, publish, reorder, slug generation, revision snapshots), `app/services/help_search_service.py` (ranked tsvector query), `app/services/help_ask_service.py` (Phase 4 retrieval + AI).
- Schemas: `app/schemas/help.py` (Pydantic request/response models).
- Routers: `app/api/v1/platform_help.py` (authoring) and `app/api/v1/public_help.py` (public).
- Register both in `app/api/v1/router.py` (the central aggregator, alongside `public_branding.router` and `platform_tenants.router`).
- Feature flag: add `ve_help_center_v1: bool = False` to `app/core/config.py` (same convention as `ve_multi_workspace_v1`, which is enforced server-side in `users.py`). This flag gates the **public read API and website exposure** during rollout; the authoring API is always gated by `require_platform_admin`. Important: the project has no generic backend-flag-to-frontend channel today (flags like `ve_multi_workspace_v1` are enforced on the server and surfaced through data, not pushed to the client), so the admin nav is NOT gated on this flag client-side - see the corrected 6.1.
- Platform settings access reuses the existing `PlatformSettingsService` (`app/services/platform_settings_service.py`) for the `help_*` keys; do not hand-roll a second settings reader.

### 5.2 Authoring API (`prefix="/platform/help"`, `tags=["platform"]`, every route `Depends(require_platform_admin)`)
Collections:
- `GET /platform/help/collections` list all (any status) with article counts.
- `POST /platform/help/collections` create.
- `PATCH /platform/help/collections/{id}` update (name, description, icon, tone, slug, publish toggle).
- `DELETE /platform/help/collections/{id}` refuses with 409 if the collection still holds articles, so a single misclick cannot silently wipe 23 articles through the `ON DELETE CASCADE`. The UI must first move or delete the articles, or the caller passes explicit `force=true` after a typed confirmation.
- `POST /platform/help/collections/reorder` accept an ordered id list (drag-and-drop persistence).

Articles:
- `GET /platform/help/collections/{id}/articles` list articles in a collection (any status).
- `GET /platform/help/articles/{id}` fetch one for editing (full body).
- `POST /platform/help/articles` create (defaults to draft; slug auto-derived from title, editable).
- `PATCH /platform/help/articles/{id}` update fields/body.
- `POST /platform/help/articles/{id}/publish` and `/unpublish` (publish sets `published_at` on first publish).
- `DELETE /platform/help/articles/{id}`.
- `POST /platform/help/articles/reorder`.
- `PUT /platform/help/articles/{id}/related` set curated related ids.
- Draft preview is rendered **inside the main app** at `/platform/help/articles/:id/preview` using the shared help renderer (see 6.4), fed by the authoring `GET /platform/help/articles/{id}` the admin is already authorized for. There is deliberately NO public draft-preview endpoint and no preview token: the public API stays strictly published-only, so a draft can never leak through it (this corrects the earlier "preview on the live site against a draft" idea, which contradicted published-only reads).
- `GET /platform/help/articles/{id}/revisions` and `POST /.../revisions/{rev}/restore` (Phase 3).

Media:
- `POST /platform/help/media` multipart upload to the `help-media` bucket; returns the public URL.

Feedback analytics (closes the loop in the UI):
- `GET /platform/help/feedback/summary` per-article 👍/😐/👎 counts and helpfulness ratio.
- `GET /platform/help/articles/{id}/feedback` recent comments for an article.

Settings:
- `GET /platform/help/settings` and `PUT /platform/help/settings` read/write the `help_*` keys in `platform_settings`.

All mutations record an entry on the **platform audit trail** (`PlatformAuditRepository` / the `platform_audit` table), with `tenant_id` left null because help content is platform-global rather than tenant-scoped. That is the correct trail for cross-tenant operator actions; `AuditService.log_lifecycle` is tenant-scoped (it requires a `tenant_id`/`tenant_slug`, which is why `platform_tenants.py` can use it - it operates on a specific tenant) and is the wrong fit for tenant-less help content.

### 5.3 Public API (`prefix="/public/help"`, NO auth dependency, published-only, PII-free)
Modeled on `public_branding.py`.
- `GET /public/help/settings` returns site title, book-a-call URL, support email, default locale, chat provider/app id (all non-secret).
- `GET /public/help/collections?locale=en` published collections with published-article counts, ordered.
- `GET /public/help/collections/{slug}?locale=en` collection plus its published articles (title, slug, excerpt).
- `GET /public/help/articles/{slug}?locale=en` one published article: title, body_md, published_at, collection crumb, seo fields. This GET performs **no write** (a write-on-GET is non-idempotent, defeats CDN caching, and is trivially inflated by bots). View counting, if wanted, is a separate fire-and-forget `POST /public/help/articles/{slug}/view` beacon, rate-limited, and is explicitly a Phase-3+ nicety rather than a launch requirement.
- `GET /public/help/articles/{slug}/related` curated related, else same-collection fallback.
- `GET /public/help/search?q=...&locale=en` ranked results (title + excerpt snippet) via `search_tsv` and `ts_rank`, published-only.
- `POST /public/help/articles/{slug}/feedback` body `{rating, comment?, path?}`. Rate-limited per `session_hash`; `comment` length-capped; never echoes PII.
- `POST /public/help/ask` (Phase 4) natural-language question; returns an answer with article citations.

The public router returns only `status='published'` (and `is_published` collections), so drafts never leak. It returns no user PII at all.

### 5.4 Search and "Ask AI"
- Phase 1 search uses Postgres full-text (`search_tsv` GIN index + `ts_rank` ordering, `ts_headline` for snippets). This is robust and needs no new infra.
- Phase 4 "Ask AI" reuses the project's existing provider-agnostic AI layer (`app/services/ai_service.py`; `SYSTEM_DESIGN.md` 1.3, admin-selected provider, never auto-switching per the project's standing rule). `help_ask_service` retrieves the top published articles for the question (full-text first; optional pgvector embeddings later), prompts the selected provider to answer grounded strictly in those articles, and returns the answer plus the cited article slugs so the widget can render citation chips like the reference. If Jake prefers, this is swapped for an embedded third-party messenger (Intercom/Crisp) via the `help_chat_provider`/`help_chat_app_id` settings, with no backend AI work.

### 5.5 Security and abuse control
- Authoring: strictly `require_platform_admin`; tenant admins and all other roles are rejected, matching the cross-tenant rule in `auth.py`.
- Public: unauthenticated but published-only and PII-free; feedback, view-beacon, and ask endpoints use the existing `build_rate_limiter` dependency from `app/core/rate_limit.py` (the same limiter the vendor public router uses), keyed on `x-forwarded-for`, and are size-capped. That limiter is in-process per task, so on multi-task Fargate it is coarse defense-in-depth; the real ceiling is enforced at CloudFront/WAF (consistent with the limiter module's own docstring). Markdown is sanitized on render (see 7.5) so even though content is admin-authored, no stored HTML can execute.
- CORS: add the help origins (`help.velvetelves.com`, `help.stage.velvetelves.com`, local dev origin) to `cors_origins` (env/secret, not a code change), so the browser-side public calls are permitted.

---

## 6. Main-app admin authoring UI

This is the surface platform admins use. It must be modern, mouse-first, minimal-typing, and fully UI-testable, and it must conform to `STYLE_GUIDE.md`.

### 6.1 Navigation and routing
- Add routes to `velvet-elves-frontend/src/utils/constants.ts` under the `PLATFORM_*` block: `PLATFORM_HELP` (`/platform/help`), `PLATFORM_HELP_COLLECTION` (`/platform/help/collections/:id`), `PLATFORM_HELP_ARTICLE_NEW` (`/platform/help/articles/new`), `PLATFORM_HELP_ARTICLE_EDIT` (`/platform/help/articles/:id/edit`), `PLATFORM_HELP_FEEDBACK` (`/platform/help/feedback`), `PLATFORM_HELP_SETTINGS` (`/platform/help/settings`).
- Register the pages in `src/App.tsx` inside the existing `<Route element={<PlatformAdminGuard />}>` block (the same block that wraps `PLATFORM_TENANTS`).
- Add a nav entry to the Platform group in `src/layouts/AppLayout.tsx` (the `isPlatformAdmin` branch around line 451): `{ to: ROUTES.PLATFORM_HELP, icon: LifeBuoy, label: 'Help center' }` (lucide `LifeBuoy` or `BookOpen`; no emoji icons, per the project's nav-icon rule). The entry is gated by `is_platform_admin` only - which the entire Platform group already is - because there is no generic backend-flag-to-frontend channel (see 5.1). The `ve_help_center_v1` flag instead gates the public read API / website exposure on the server. If a hard client gate is later required, surface the flag through the help settings payload the admin pages already fetch (`GET /platform/help/settings`), not through an imagined global flags endpoint.
- This authoring surface is distinct from the existing `/settings/help` page (`SETTINGS_HELP`), which is a per-user "Help & Tour" shortcut (replay the guided tour, reach support) and is unrelated to managing knowledge-base content.

### 6.2 Collections management page (`/platform/help`)
A Collection / list (CRUD) page per `STYLE_GUIDE.md` 15.4 (canonical refs `TaskTemplateListPage.tsx`, `TeamMembersTable.tsx`):
- Shell: full-width admin shell, `PlatformPageHeader` (breadcrumb "Platform > Help center", serif title, a count badge, and a "New collection" primary in the trailing slot).
- Optional stat strip: total collections, total published articles, helpfulness ratio, drafts pending (vary tone across the cards, do not ship four grey cards).
- Table: each row is a collection with its icon tile, name, description, article count, a published SegmentedControl, and inline edit/delete actions (destructive via `useConfirm()` + toast). Rows are drag-reorderable; the order persists via the reorder endpoint.
- Clicking a row opens the collection's Articles page.
- Create/edit a collection uses the flat modal anatomy (`STYLE_GUIDE.md` 6.5): serif title, hairline-divided sections, sentence-case labels, `Select` for the lucide icon (with a small visual preview of the tile), `SegmentedControl` for Published/Draft, `Textarea` for the description. Only the name/description are typed; everything else is a click.

### 6.3 Articles list (per collection)
Same collection-table pattern: title, status pill (Draft/Published/Archived), updated date, drag-reorder, inline Publish/Unpublish toggle, inline edit (opens the editor), inline delete. "New article" primary in the header. Honest empty state with an inline "New article" CTA.

### 6.4 Article editor (`/platform/help/articles/:id/edit`) - the core authoring experience
This is a record with one large body field, so it is a **full-page two-pane editor**, not a small modal (the modal-vs-inline rule in `STYLE_GUIDE.md` 6.5 reserves modals for small/medium records; a long-form body needs room and a live preview):
- Left pane (the form + writing surface):
  - Title (typed), auto-derived slug (editable, click to override).
  - Collection picker (`Select`), Status (`SegmentedControl`: Draft / Published / Archived), Excerpt (`Textarea`).
  - A Markdown editor with a **formatting toolbar** so writing is mouse-first: Bold, Italic, H2/H3, bullet/numbered list, link, quote, and **Insert image** (drag-drop or click, uploads to `help-media`, inserts the URL). Typing is only ever the actual prose.
  - Related articles: a multi-select of other published articles (click to add/remove, drag to order).
  - SEO (collapsible): SEO title and description.
- Right pane (live preview): the body rendered with the **shared help renderer** (`HelpArticleBody`) so the admin sees the real reader output as they type, serving the standing lesson to verify rendered output, not just the mechanism. Because the main app and the help-center site are separate projects, `HelpArticleBody` (its react-markdown component map + plugin set) is one small module kept **byte-identical in both repos** (a deliberately-synced copy, or an optional shared npm package if a monorepo workspace is preferred); it is NOT a literal cross-repo import. The current frontend uses plain react-markdown with no GFM (see `src/components/agent/AgentMarkdown.tsx`), so this renderer adds `remark-gfm`, `rehype-slug`, and `rehype-sanitize` as new dependencies in BOTH projects - they are not currently installed in `velvet-elves-frontend`.
- Action bar: Save draft, Publish/Unpublish (one decisive click), and "Preview" (opens the in-app preview route `/platform/help/articles/:id/preview`, which renders the draft with the shared help renderer - no website round-trip, no draft ever exposed publicly). Saving is optimistic with a global "Saving..." indicator and an Undo affordance for destructive steps, per the comfort scale.

### 6.5 Feedback page (`/platform/help/feedback`)
A page (standard admin shell) listing articles by helpfulness, with the 👍/😐/👎 counts and a drill-in to recent comments. This makes reader sentiment fully visible and actionable in the UI, and gives testers a place to confirm that feedback they submitted on the public site arrived.

### 6.6 Help-center settings page (`/platform/help/settings`)
A centered config page (the personal-config settings shape) editing the `help_*` keys: site title, Book-a-Call URL, support email, default locale, chat provider (`Select`: None / Ask AI / Intercom / Crisp) and chat app id. Saved through the settings endpoint.

### 6.7 Data fetching
React Query hooks mirroring `src/hooks/usePlatformTenants.ts`: `useHelpCollections`, `useHelpArticles`, `useHelpArticle`, `useHelpFeedbackSummary`, `useHelpSettings`, plus mutations for create/update/publish/reorder/delete. Optimistic updates for reorder and publish.

### 6.8 Design conformance
Everything uses `ve-*` tokens, the three-voice type hierarchy (serif titles, sans body, mono kickers), `shadow-card`, `rounded-xl` cards, flat modals (6.5), one-line filter+search bars (9.3), `Select`/`SegmentedControl` (never native controls), and lucide icons. No text below 12px; no meaning carried by the smallest size. The result reads as a professional content tool, not a generic CMS.

---

## 7. The separate help-center website (`c:\Projects\velvet-elves-help-center`)

A standalone project that consumes the public API. The exact folder is `c:\Projects\velvet-elves-help-center` (the user wrote "Project/velvet-elves-help-center"; the real sibling path next to `velvet-elves-backend` / `velvet-elves-frontend` is `c:\Projects\velvet-elves-help-center`).

### 7.1 Stack (chosen to harmonize and to fit the existing deploy model)
Vite + React 18 + TypeScript + Tailwind, the same stack as `velvet-elves-frontend`. Rationale:
- It reuses the project's `ve-*` Tailwind tokens and fonts verbatim, so the help center looks like part of the product.
- The AWS plan already treats the help center as a static S3 + CloudFront surface (the same shape as the frontend's `dist`), so a Vite static build drops straight in.
- Testers and developers already know this stack, reducing workflow breakage.

Alternative considered and rejected: a Next.js SSR app would give server-rendered SEO out of the box, but it diverges from the project's stack and from the static S3+CloudFront model the AWS plan specifies for `help.velvetelves.com`. I instead get SEO from a build-time prerender step (7.6) while keeping the simpler static deploy. I will confirm this with Jake (Q4).

### 7.2 Dependencies
`react`, `react-dom`, `react-router-dom`, `@tanstack/react-query`, `react-markdown`, `remark-gfm`, `rehype-slug`, `rehype-autolink-headings`, `rehype-sanitize`, `lucide-react`, `clsx`, `tailwind-merge`. Dev: `vite`, `@vitejs/plugin-react`, `typescript`, `tailwindcss`, `postcss`, `autoprefixer`, and a prerender helper (`vite-react-ssg` or a small Puppeteer/prerender script).

### 7.3 Project layout
```
velvet-elves-help-center/
  index.html
  package.json
  vite.config.ts
  tailwind.config.js        # copy theme.extend.colors.ve + fonts from the frontend
  postcss.config.js
  .env.example              # VITE_HELP_API_BASE_URL=...
  public/                   # logo, favicon, fonts (IBM Plex Sans/Mono, Lora)
  src/
    main.tsx
    App.tsx                 # router + QueryClientProvider
    index.css               # ve-* CSS variables + base type (copied from frontend)
    lib/api.ts              # typed fetch client for /public/help/*
    lib/markdown.tsx        # react-markdown config (GFM, slug, sanitize, ve styles)
    lib/toc.ts              # build TOC from headings
    components/
      TopBar.tsx            # logo, Book a Call, language selector
      HeroSearch.tsx        # navy gradient hero + search box
      CollectionCard.tsx
      ArticleListItem.tsx   # title + snippet (search + collection)
      ArticleBody.tsx       # rendered markdown
      TableOfContents.tsx   # right rail, scroll-spy active section
      RelatedArticles.tsx
      FeedbackWidget.tsx    # 3 emoji reactions + optional comment
      Footer.tsx            # Book a call / Email us
      ChatWidget.tsx        # Ask AI panel OR third-party embed
      Breadcrumbs.tsx
    pages/
      HomePage.tsx
      CollectionPage.tsx
      ArticlePage.tsx
      SearchResultsPage.tsx
      NotFoundPage.tsx
```

### 7.4 Routes and pages
- `/` Home: `TopBar` + `HeroSearch` + the collections list (`CollectionCard` per published collection). Matches Screenshot_21/22/23.
- `/collections/:slug` Collection: hero header retained, breadcrumb, the collection's published articles as a list.
- `/articles/:slug` Article: breadcrumb ("All Collections > {Collection} > {Title}"), title, date, rendered body, right-rail `TableOfContents` with scroll-spy, `RelatedArticles`, `FeedbackWidget`, `Footer`. Matches Screenshot_53/54.
- `/search?q=...` Search results: `ArticleListItem` rows (title + snippet). Matches Screenshot_52.
- `*` Not found.

### 7.5 Rendering and safety
`lib/markdown.tsx` configures react-markdown with `remark-gfm`, `rehype-slug` (heading ids for the TOC and anchor links), `rehype-autolink-headings`, and `rehype-sanitize`. The sanitize schema is extended to **permit `id` on headings** (so the TOC anchors survive sanitization) and **`img` whose `src` is the `help-media` public-bucket origin** (so embedded screenshots render) while still stripping scripts and event handlers. The article body styling uses the `ve-*` tokens (serif headings via Lora, sans body, hairline rules, generous line-height) so the reading experience matches the product. This renderer is the `HelpArticleBody` module kept byte-identical with the main app's editor preview (6.4) - a synced copy across the two repos, not a literal shared import - so the admin sees precisely what readers see.

### 7.6 SEO
- A build-time prerender step fetches the list of published collections and articles from the public API and emits a static HTML file per route (so crawlers and link previews get real content and meta tags), while runtime stays a fast SPA.
- A generated `sitemap.xml` and per-article `<title>`/meta-description (from the article SEO fields), Open Graph tags, and canonical URLs.
- Because content changes are infrequent and publishing is an explicit admin action, prerender runs on each deploy; a later enhancement can trigger a rebuild on publish.

### 7.7 Visual design (matching the reference, harmonized with the brand)
- Hero: navy gradient built from `ve-sidebar` (#1E3356), white serif site title, a large rounded search field. This reuses the brand's existing navy rather than inventing a new one.
- Collection cards: `rounded-xl border border-ve-border bg-white shadow-card`, a green-tinted rounded-square icon tile (`ve-green-bg` with a lucide glyph) matching the reference's green tiles, serif title, muted description, mono "N articles" count.
- Article typography: Lora serif headings, IBM Plex Sans body at a comfortable reading size (15px+, line-height 1.6 per the v2 comfort scale), hairline dividers, right-rail TOC with the active item in champagne (`ve-orange`).
- Feedback widget and footer styled to the reference, in brand tokens.
- The whole site obeys the comfort rules: nothing below 12px, AA contrast, calm motion (150 to 250ms ease-out, no bounce).

### 7.8 Configuration and API client
`VITE_HELP_API_BASE_URL` is a build-time value (per the AWS plan's note that Vite env is build-time) pointing at the environment's API host (`api.stage.velvetelves.com` or `api.prod.velvetelves.com`). `lib/api.ts` calls only `/public/help/*`. The site fetches `/public/help/settings` on load to get the title, Book-a-Call URL, support email, default locale, and chat config.

---

## 8. AI support widget, Book a Call, Email us, and language

### 8.1 Chat / Ask AI (the reference's messenger)
Two supported modes, selected by the `help_chat_provider` setting:
- `ask_ai` (the "distinctly professional tool" option): the `ChatWidget` posts to `/public/help/ask`, which grounds an answer in published articles using the project's existing AI provider layer and returns citations the widget renders as numbered source chips with links into the cited articles, mirroring Screenshots_24/25/26. Phased to Phase 4.
- `intercom` / `crisp`: the `ChatWidget` simply injects the third-party messenger using `help_chat_app_id`. This delivers the visual/functional parity of the reference (which is itself a third-party messenger) with no AI build, and is the recommended Phase-1 stand-in.
- `none`: the launcher is hidden.

### 8.2 Book a Call and Email us
`TopBar` and `Footer` render a "Book a Call" link (`help_book_a_call_url`, e.g. a Calendly URL) and an "Email us" link (`mailto:` from `help_support_email`). Both are managed in the admin Help-center settings, so non-developers change them through the UI.

### 8.3 Language selector
The schema is locale-aware from day one (`locale` + `translation_group` on articles and `locale` on collections), and the public API accepts `?locale=`. Phase 1 ships English only: the selector either shows just English or is hidden until a second locale exists (Q2 for Jake). When a locale is added, an admin authors translated rows linked by `translation_group`, and the selector switches the reader between them with no rework. This keeps the workflow seamless rather than retrofitting i18n later.

---

## 9. Deployment

This slots into `AWS_ECS_CLOUDFRONT_PRODUCTION_DEPLOYMENT_PLAN.md`, which already reserves the help domains and classifies the help center as a separate web surface.

- Domains (already reserved by the AWS plan): staging `help.stage.velvetelves.com`, production `help.velvetelves.com`.
- Hosting: an S3 bucket per environment plus a CloudFront distribution, with SPA fallback to `index.html` and, like the frontend, correct MIME handling for `.mjs` if any worker assets are used. ACM certificate in `us-east-1` for the CloudFront alias; GoDaddy DNS record to the distribution (the AWS plan keeps DNS in GoDaddy for now).
- Backend CORS: add the help origins to `cors_origins` for each environment (env/secret change, not code).
- CI/CD: a workflow inside `velvet-elves-help-center` mirroring the project's branch model (`develop` local, `main` staging, `prod` production): build with the environment's `VITE_HELP_API_BASE_URL`, sync `dist` to the env S3 bucket, and invalidate CloudFront. The prerender step (7.6) runs in the build before sync.
- Content freshness vs caching (critical for the tester workflow "publish, then see it live"): CloudFront caches the SPA's static assets and the prerendered HTML (rebuilt each deploy, for crawlers and link previews). The **public help API responses are served with a short or `no-cache` policy** - and the API is not behind the website's CloudFront - so client-side navigation always fetches live published content and the SPA overrides any stale prerendered HTML on hydration. This is why an admin who publishes an article sees it immediately when browsing the site, without waiting for a redeploy or a CloudFront invalidation. Only the raw first-paint HTML for a brand-new article URL (before the next prerender) lags, and that path is for crawlers, not the interactive reader.
- The backend migration (Section 4) ships through the existing Supabase migration step of the main app's pipeline. The authoring UI ships with the main frontend behind `ve_help_center_v1`.

---

## 10. Phased delivery plan

Each phase is independently shippable and ends at a gate that a non-developer can verify in the UI. The public website can stay dark (or password-gated at CloudFront) until Phase 3.

### Phase H0 - Foundation (backend + flag)
- Migration (Section 4): tables, RLS, indexes, `help-media` bucket, seeded `help_*` settings.
- Models, repositories, services, schemas; authoring and public routers registered; `ve_help_center_v1` flag added (default off).
- Gate: Swagger shows the endpoints; with the flag on, a platform admin can create a collection and an article via the API and read it back via the public endpoint; a non-admin token is rejected on authoring routes.

### Phase H1 - Admin authoring UI
- Collections page, articles list, the two-pane article editor with toolbar + live preview + image upload, publish/unpublish, reorder, related articles, settings page, feedback page. Nav entry in the Platform group behind the flag.
- Gate (UI-only): a platform admin creates the reference's starter collections, writes an article using only the toolbar and one drag-dropped image, and sees it faithfully in the **in-app preview** (`/platform/help/articles/:id/preview`). The public website does not exist until H2, so "preview on the live site" is an H2 gate, not an H1 one. All of this without touching code or the database.

### Phase H2 - Public website (read + search + feedback)
- The separate Vite project: Home, Collection, Article (TOC + related), Search, feedback submission, Book-a-Call/Email links. Reuses `ve-*` tokens.
- Gate (UI-only): on the running site, the tester sees the published collections, opens an article, scrolls and watches the TOC track, follows a related link, searches and gets ranked title+snippet results, and submits a 👍 that then appears on the admin Feedback page.

### Phase H3 - SEO, revisions, polish, and go-live
- Build-time prerender + sitemap + meta tags; article revision history + restore; staging validation; production cutover to `help.velvetelves.com`.
- Gate: a published article URL returns correct title/meta in view-source on staging; restoring a prior revision works from the UI; the production domain serves the site over HTTPS.

### Phase H4 - AI support widget (optional, decision-gated)
- Either wire the `ask_ai` endpoint + `ChatWidget` with citations (reusing the existing provider-agnostic AI layer), or finalize the third-party embed. Decided by Jake (Q1).
- Gate: a reader asks a question in the widget and gets an answer with working citation links into published articles (or the embedded messenger loads and connects).

---

## 11. End-to-end UI test script (for non-developer testers)

All steps are mouse-first and validated entirely through the UI, so a real-estate professional can run them without developer help. This is the workflow the plan is engineered to keep unbroken.

Authoring (in the main app, as a platform admin):
1. Open the sidebar Platform group and click "Help center". Expect the Collections page with a "New collection" button.
2. Click "New collection", pick an icon from the dropdown, type a name and one-line description, set Published, Save. Expect the new collection card in the table.
3. Open the collection, click "New article", type a title (watch the slug fill in), choose the collection, write a few lines using the Bold and bullet-list toolbar buttons, drag in an image. Expect the right-hand live preview to match as you type.
4. Click "Publish". Expect the row's status pill to read Published.
5. Click "Preview". Expect the in-app preview route to render the article exactly as the right-hand pane showed. (Before Phase H2 there is no public site yet; the "open the live help center" steps 7-12 are the full end-to-end run once H2 ships.)
6. Open Help-center settings, set the Book-a-Call URL and support email, Save.

Reading (on the separate website):
7. Open the help center home. Expect the navy hero, the search box, and the published collection card with its article count.
8. Open the collection, then the article. Expect the breadcrumb, the date, the body, and a right-rail table of contents that highlights the section you scroll to.
9. Click a related article link. Expect it to navigate correctly.
10. Search for a phrase from the article. Expect a ranked result showing the title and a snippet; click it to open the article.
11. Click the happy face under "Did this answer your question?", optionally type a comment, submit. Expect a thank-you state.
12. Click "Book a call" and "Email us". Expect the configured URL and the mail composer.

Loop closure (back in the main app):
13. Open the admin Feedback page. Expect the 👍 you submitted (and any comment) to appear against that article.

If any step requires editing code, a config file, or the database directly, the workflow has failed its design goal and must be fixed before sign-off.

---

## 12. Security, privacy, and integrity checklist
- Authoring endpoints are all `Depends(require_platform_admin)`; tenant Admins and every non-platform role are rejected (consistent with `auth.py`). The admin routes are also 404-guarded client-side by `PlatformAdminGuard` so the route tree does not leak.
- Public endpoints are unauthenticated, return only published, PII-free content, and never expose drafts.
- Reader markdown is sanitized on render (`rehype-sanitize`); uploaded media goes only to the `help-media` bucket via the service-role write path.
- Feedback and Ask endpoints are rate-limited per hashed session and size-capped.
- All content mutations are audited via the existing `AuditService` lifecycle log.
- RLS is service-role-only on every new table, matching `platform_settings`.

---

## 13. Open decisions for Jake
- Q1 (Chat): Build the in-house "Ask AI" widget with citations (reuses our AI layer, most on-brand) or embed a third-party messenger (Intercom/Crisp) to match the reference exactly with less effort?
- Q2 (Language): Launch English-only with the selector hidden, or stand up a second locale at launch? (Schema supports both regardless.)
- Q3 (Support links): Confirm the Book-a-Call URL and the support email address.
- Q4 (Stack): Confirm the Vite static + build-time-prerender approach for `help.velvetelves.com` (my recommendation), versus a Next.js SSR site.
- Q5 (Access): Is the help center fully public to the world, or password-gated at CloudFront until launch?
- Q6 (Starter content): Should I provide a one-click "Import starter collections" that creates the reference's category skeleton (Getting Started, Navigation & Dashboard, Contacts & Parties, Email, Documents) as drafts for editing, rather than starting from an empty back office?
- Q7 (White-label, future): Do individual brokerages (tenants) ever get their own branded help center, or is there one platform-wide help center? (This plan assumes one platform-wide help center, owned by platform admins.)

---

## 14. Out of scope (future)
- Per-tenant white-labeled help centers on custom domains.
- Full AI-agent parity with a commercial messenger (conversation memory, human handoff, ticketing).
- Scheduled publishing, A/B testing of articles, and advanced content analytics beyond the helpfulness summary.
- In-app contextual help deep-linking from specific product screens into specific articles (a natural follow-on once the article slugs are stable).

---

## 15. Why this plan will not break in testing
It is grounded in the actual codebase rather than assumptions: it reuses `require_platform_admin`, the `public_branding.py` public-router pattern, the `platform_settings` store via `PlatformSettingsService`, the `platform_audit` trail, the `build_rate_limiter` dependency, the in-migration storage-bucket pattern, the Supabase service-role migration style, the `PlatformAdminGuard` / `PlatformPageHeader` / Platform-nav conventions, the `ve-*` design system, and the AWS plan's reserved help domain and static-surface deployment model. The governing constraint (platform-admin-managed content) is satisfied by existing auth primitives, not new ones. Every deliverable ends at a gate a non-developer verifies through the UI, and the admin editor renders articles with the byte-identical `HelpArticleBody` renderer the public site uses, so what an author sees is what a reader gets.

---

## 16. Review log and corrections (2026-06-25)

A second pass re-checked every workflow/logic claim against the live source and the `velvet-elves-data` docs. The following flaws were found and are now corrected in the body above. Each is a place where the original draft would have broken an end-to-end flow or assumed a pattern the code does not have.

1. Audit path (5.2). The draft used `AuditService.log_lifecycle`, which is tenant-scoped and requires `tenant_id`/`tenant_slug`. Help content is platform-global. Corrected to the `platform_audit` trail via `PlatformAuditRepository` with `tenant_id` null (both confirmed present: `app/models/platform_audit.py`, `app/repositories/platform_audit_repository.py`).
2. Feature-flag exposure to the client (5.1, 6.1). The draft gated the admin nav on `ve_help_center_v1`, but the codebase has no backend-flag-to-frontend channel (`ve_multi_workspace_v1` is enforced in `users.py` and surfaced through data). Corrected: the nav is gated by `is_platform_admin` (as the whole Platform group already is); the flag gates server-side public exposure only.
3. Draft preview contradiction (5.2, 6.4, 10, 11). The draft proposed previewing an unpublished draft on the live public site, which contradicts the published-only public API, and it sequenced that preview into Phase H1 before the website exists (H2). Corrected to an in-app preview route rendered by the shared renderer; no public preview endpoint or token.
4. Cross-repo "same component" impossibility (6.4, 7.5). Two separate projects cannot import one React component. Corrected to a `HelpArticleBody` module kept byte-identical in both repos (synced copy, optional shared package), and called out that `remark-gfm` / `rehype-slug` / `rehype-sanitize` are NOT in `velvet-elves-frontend` today (it uses plain react-markdown per `AgentMarkdown.tsx`) and must be added to both.
5. Write-on-GET view counter (4.2, 5.3). Incrementing `view_count` on every public article GET is non-idempotent, defeats CDN caching, and is bot-inflatable. Corrected to no write on GET; counting is an optional rate-limited beacon, Phase 3+.
6. Content freshness vs CloudFront caching (9). The draft never reconciled a cached static site with the "publish then immediately see it live" tester step. Corrected with an explicit cache policy: assets/prerender cached, public API short/`no-cache`, SPA overrides stale prerender on hydration.
7. Storage bucket provisioning (4.7). The draft hand-waved bucket creation. Corrected to an in-migration `storage.buckets` insert plus service-role and public-read policies, mirroring `20260506_logos_bucket.sql`.
8. Rate-limiting infra (5.5). Corrected from a vague "rate-limited per hashed session" to the actual `build_rate_limiter` dependency in `app/core/rate_limit.py`, with the honest caveat that it is in-process per Fargate task and CloudFront/WAF is the real ceiling.
9. Platform settings reader (5.1). Now reuses the existing `PlatformSettingsService` rather than implying a new one.
10. Collection-delete footgun (5.2). `ON DELETE CASCADE` plus a delete button could wipe a full collection of articles on one click. Corrected to a 409 guard unless the collection is empty or `force=true` is passed after a typed confirmation.
11. Slug stability (4.2). Added the rule that a published article's slug is frozen (no silent re-slug on title edits) to avoid breaking live URLs.
12. Search snippet quality (4.2). Noted that the public snippet is built from `excerpt`, with an optional Markdown-stripped shadow column as a later refinement, rather than surfacing raw Markdown in `ts_headline`.
13. Surface collision (6.1). Clarified that this is distinct from the existing per-user `/settings/help` "Help & Tour" page, so the two are not confused during implementation.

No item in this review changes the governing constraint or the three-surface architecture; the corrections harden the workflow so it does not break under a non-developer's UI test.
