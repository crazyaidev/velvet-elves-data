# Milestone 5.3 — Profiles & Advanced Features
## Comprehensive Implementation Plan

| | |
| --- | --- |
| Milestone | **5.3 — Profiles & Advanced Features** (Week 19, 2026-07-13 → 2026-07-19) |
| Phase | Phase 5 — Dashboards, Payments & Profiles |
| Plan version | **2.1 (2026-05-28 — Profile-as-Modal.** Identity surface converted from a standalone page to a shared modal (`ProfileModal`) invoked from the avatar menu across all roles. The change is small relative to v2.0's substance — same field set, same backend — but it removes three routes, eliminates the empty `pages/profile/` directory, and naturally folds the M5.1 Reports tab into the canonical `/analytics` page where it belongs.) |
| v2.0 → v2.1 changelog | (1) `/profile`, `/client/profile`, `/fsbo/profile` routes removed; replaced by a single shared `ProfileModal` opened from each role's avatar menu. (2) The existing M5.1 "Reports" tab on `/profile` migrates to `/analytics` (where the same per-user analytics already live in expanded form — minor M5.1 cleanup ticket inside M5.3). (3) `FRONTEND_UI_WORKFLOW_LOGIC.md §11.1` will need a spec update from "Page" to "Modal" — flagged as Risk #24. (4) Routing-constants change: drop `PROFILE`, `CLIENT_PROFILE`, `FSBO_PROFILE`; keep only Settings + Admin routes. (5) Component-count reduction: one `ProfileModal.tsx` replaces three page components. All other v2.0 sections (Settings extension, Admin team-config pages, Brokerage Overview, the four cross-cutting features) are unchanged. |
| v1.0 → v2.0 changelog (historical) | (1) Brokerage Profile moved from `/brokerage` to `/admin/brokerage` and renamed **Brokerage Overview**. (2) Profile reverts to identity surface — Personal Info only (no tabs). (3) Five new Settings sections absorb personal-preference work. (4) Five new Admin pages absorb team/tenant-wide work. (5) Client / FSBO portals split identity (Profile) + preferences (Settings). (6) The mis-added "Reports" tab removed from the implementation plan (later folded into `/analytics` per v2.1). |
| Authoritative sources | `milestones.txt` §5.3 · `requirements.txt` §1.4 (Brokerage Profiles), §1.5 (Agent/Team Profiles), §1.6 (Onboarding), §1.7 (Client & FSBO Portals), §2.6 (Workspaces), §4.4 (Dynamic Task Intelligence), §4.5 (Recommendation Transparency), §4.6 (Feedback Loop), §4.10 (AI-Generated Closing Checklists), §6.6 (In-App Notifications), §8.2 (Natural-Language Task Creation), §8.5 (Audit Logging for AI), §10.5 (Admin UI), §10.6 (Intelligence Section UI Requirements), §14.1 (Workflow Logic) · `SYSTEM_DESIGN.md` §3.2 endpoints for `/ai/suggestions`, `/notifications`, `/analytics/profile-report` · `FRONTEND_UI_WORKFLOW_LOGIC.md` §3.5 Administrator Dashboard, §4.1 Active Transactions (AI suggestion panel, Print Checklist footer), §6.1 AI Suggestions, §6.3 Settings (as-built, May 2026), §8.1 FSBO Overview, §9.4 Client Agent Info, §10 (Admin section), §11.1 Profile, §13 Workflow L (Profile & Settings), §14 Global Patterns 5 (Print Closing Checklist) & 8 (AI Confidence Indicators) |
| Approved HTML references | `completed_designs/ve-intelligence-ai_suggestions.html` (canonical AI Suggestions design). No HTML mock exists for Profile, Settings extensions, Brokerage Overview, Team admin pages, Checklist Editor, or NLP Task Modal — these are designed in-flight against `STYLE_GUIDE.md` and the visual-consistency anchors. |
| Visual-consistency anchors | `components/users/UserForm.tsx` (existing edit-form logic — refactored into `ProfileModal` body) · `pages/settings/SettingsPage.tsx` (canonical eight-section scrolling document with sticky left-rail nav — extend to thirteen sections) · `pages/admin/AdminAIGovernancePage.tsx` (admin section header pattern) · `pages/admin/AdminPaymentAccessPage.tsx` (admin role-toggle layout) · `pages/dashboards/AdminDashboardPage.tsx` (admin landing — entry-point host for Brokerage Overview tile) · `pages/dashboards/SoloAgentDashboardPage.tsx` (existing Print Checklist deep-link in expanded card footer — the surface through which the new checklist generator becomes user-reachable) · `components/ui/dialog.tsx` (Radix `<Dialog>` primitive — host for `ProfileModal`) |
| External dependencies | None new. Reuses existing AI provider abstraction, Supabase Storage, print flow, and email service. |
| Out-of-scope (handled elsewhere) | M2.2 task generation engine · M3.x AI document parsing · M4.x email automation · M5.1 dashboard landing pages · M5.2 payment surfaces · M6.1 white-label branding configuration UI · M6.2 advertising hooks |

---

## 0. Strategic Realignment (v2.0 + v2.1)

### 0.1 The v1.0 mistake

The v1.0 plan proposed extending the Profile page (`/profile`) from its current two tabs (Personal info + Reports) to a **seven-tab surface** carrying:

1. Personal Info
2. Notifications
3. Checklist Templates
4. Tagged Notes
5. Preferred Vendors
6. Internal Resources
7. Reports

It also proposed creating a top-level `/brokerage` route and hiding team-wide configuration behind an "Inherit from team" toggle inside the per-user Profile.

This is wrong for four reasons:

| # | Symptom | Root cause |
| --- | --- | --- |
| 1 | Profile and Settings become two parallel preference surfaces | The plan conflated **identity** (who I am) with **preferences** (how the system behaves for me). Notifications, templates, vendor lists, and resource libraries are preferences — they belong on Settings. |
| 2 | Team-wide configuration hides inside personal pages | Team checklist templates, team preferred vendors, team tagged notes, and team internal resources affect every member of a team. A Team Lead editing these is performing an **admin** action; surfacing it on the *member's* personal Profile (via an "Inherit" toggle) obscures the actor, the audit trail, and the user's mental model. |
| 3 | Brokerage Overview is mis-placed under the "Team" sidebar group | The page's content (KPIs, agent directory, team roster, drill-down to `/admin/users/:id`) is purely management. Peer-of-Active-Transactions placement implies it's an operational workspace. It's not — it's an admin landing. |
| 4 | A "Reports" tab is added to Profile that duplicates `/analytics` (M5.1) | The M5.1 work already shipped `/analytics` for per-agent / team / tenant-wide analytics. Adding a Reports tab to Profile is duplication and creates two routes for the same job. |

### 0.2 The v2.0 correction — three-surface mental model (v2.1 refines Profile to a modal)

> **⚠ Updated by the May 2026 redesign — see `ACCOUNT_MODAL_REDESIGN_PLAN.md`.** The three-surface *mental model* (identity / preferences / admin) still holds, but the surfaces were re-composed: **Profile + the personal Settings sections + the Client/FSBO settings pages are now one shared Account modal**, and **tenant configuration moved to a dedicated `/organization` page**. Also: Brokerage Overview was merged into Team Overview (`/team`) and the duplicate Settings → Task Templates stub was deleted. The deliverable mapping in §2.1 is unchanged; only the host surfaces differ.

Every M5.3 deliverable maps to **exactly one** of three surface categories:

| Surface | Question it answers | M5.3 contents |
| --- | --- | --- |
| **Profile** (`ProfileModal` — opens from each role's topbar avatar menu) | "Who am I?" | Personal Info **only** (name, email, phone, bio, avatar, company). One shared modal across all roles. ~480 px wide. No tabs. No URL. (v2.1: was a standalone page in v2.0; converted to a modal because the surface is small enough that a route is overhead.) |
| **Settings** (`/settings`, `/client/settings`, `/fsbo/settings`) | "How should the system behave for me?" | Personal preferences. Extends the existing seven-section scrolling document with five new sections (Notifications, My Closing Checklist Templates, My Tagged Notes, My Preferred Vendors, My Internal Resources). |
| **Admin** (`/admin/*`) | "How should the team / tenant be configured?" | Team / tenant-wide configuration. Five new admin pages: Brokerage Overview, Team Checklist Templates, Team Vendors, Team Tagged Notes, Team Internal Resources. |

This separation is **the single most important architectural decision in M5.3.** Every subsequent section of this plan is organized around it. The v2.1 modal-vs-page choice for Profile is implementation detail under that architecture, not a change to it.

### 0.3 What this changes — and what it does NOT change

What changes (frontend surface placement):

- **Profile becomes a shared `ProfileModal`** — invoked from every role's topbar avatar menu (internal, Client, FSBO). No standalone route, no tabs. The modal carries the same fields as the v2.0 page: name, email (read-only), phone, bio, company, avatar.
- The existing M5.1 **Reports tab** (currently on `/profile`) **moves to `/analytics`** — per-user analytics already live there in expanded form; the tab was a duplicate. Small M5.1 cleanup ticket inside M5.3.
- The Settings page grows from eight sections to **thirteen sections**, all consistent with the existing scrolling-document pattern with sticky left-rail nav.
- Five new Admin pages are added under `/admin/brokerage`, `/admin/team-checklist-templates`, `/admin/team-vendors`, `/admin/team-tagged-notes`, `/admin/team-internal-resources`.
- Client / FSBO portals each gain a Settings page (`/client/settings`, `/fsbo/settings`) — and access the shared `ProfileModal` from their avatar menus (no role-specific Profile pages).

What does NOT change from v2.0:

- All eight deliverables in `milestones.txt` §5.3 still ship. None are descoped.
- The AI Closing Checklist Generator, NLP Task Creation, Dynamic Task Intelligence UI, and Post-Closing Feedback Loop are unchanged.
- Backend services, database schema, audit logging, AI provider abstraction usage are unchanged. The Profile-as-modal change is purely frontend.
- The whitelisted Profile fields (`agent_bio`, `closed_transaction_reminders`, `milestone_sharing_defaults`, etc.) and their PATCH endpoint at `/api/v1/users/me` are unchanged — the modal calls exactly the same endpoint the page would have called.

### 0.4 Why this matters operationally

- **A Team Lead who needs to edit team checklist templates** no longer has to log in as each agent. They go to `/admin/team-checklist-templates`, edit once, and every agent inherits. The audit log clearly records "Team Lead X edited Team Buyer Template" — not "Agent Y's profile was modified."
- **A Client who opens Settings** sees only what they can configure (notifications, sharing). Their Agent BIO card lives there too — read-only, but contextual to "this is the agent whose notifications I'm tuning."
- **A non-developer tester navigating the app** can predict where to find anything: identity in Profile (avatar menu modal), my preferences in Settings, team/tenant configuration in Admin. No tab-hunting, no hidden inheritance toggles.
- **An agent editing their bio mid-task** doesn't lose their place in Active Transactions — the modal opens over the current page, they save, it closes, they continue.
- **Future milestones** that add preferences (e.g., M6.1 tenant branding) land on Settings or Admin naturally without growing the Profile modal further.

---

## 1. Executive Summary

Milestone 5.3 ships the **personalization layer** of Velvet Elves under the v2.0 three-surface model (§0) with the v2.1 Profile-as-Modal refinement:

1. **Brokerage Overview** at `/admin/brokerage` (TL+Admin) — single-page snapshot of all agents and teams, drill-down into existing `/admin/users/:userId` and team filters. Read-mostly; CRUD remains at the existing admin pages.
2. **Profile Modal** — a shared `ProfileModal` opened from every role's topbar avatar menu (internal, Client, FSBO). Identity only: name, email (read-only), phone, bio, company, avatar. No route, no tabs. The existing M5.1 Reports tab moves to `/analytics`.
3. **Settings page extension** at `/settings` — five new sections added to the existing scrolling document: **Notifications** (matrix + Closed-Tx Reminders sub-card), **My Closing Checklist Templates** (Buyer + Seller personal templates), **My Tagged Notes**, **My Preferred Vendors**, **My Internal Resources**. The existing Email Integrations / E-Signature / Branding / AI Configuration / Task Templates link / Help & Tour / Danger Zone sections stay where they are; the new sections insert in a logical sort order documented in §6.C.
4. **Admin team-configuration pages** — four new TL+Admin pages: `/admin/team-checklist-templates`, `/admin/team-vendors`, `/admin/team-tagged-notes`, `/admin/team-internal-resources`. Each is a single-card admin surface that follows the existing `AdminPageHeader` + form pattern. Team-level values are inherited by members whose own Settings value for the same key is empty — but the inheritance happens **server-side**, transparently. The user does not see an "Inherit" toggle on their personal Settings; they see the resolved value with a small caption "Provided by your team — override in Settings" when applicable.
5. **Client Portal** — gains `/client/settings` (notification preferences, milestone-sharing defaults, read-only Agent BIO card). Identity edits use the shared `ProfileModal` from the avatar menu.
6. **FSBO Portal** — gains `/fsbo/settings` (notification preferences, milestone-sharing defaults, support/guide contact preferences, FSBO boundary notice). Identity edits use the shared `ProfileModal`.
7. **AI Closing Checklist Generator** (`PrintChecklistModal` + backend extension) — Agent Sheet + Client Sheet, sourced from the user's Settings → My Checklist Templates and Settings → My Internal Resources. Reachable from every existing Print Checklist entry point (Solo Agent dashboard, Team Leader dashboard, Active Transactions card footer, Transaction Detail, Settings → My Checklist Templates "Preview").
8. **Natural-Language Task Creation** (`AiNlpTaskModal`) — "✦ Quick add" button on Active Transactions drawer and `/tasks/queue`. Two-step modal (NL textarea → review parsed payload → save).
9. **Dynamic Task Intelligence UI** — `/ai-suggestions` page rebuild + per-deal AI Suggestions strip + Team Lead Bulk Accept preview modal.
10. **Task Feedback Loop UI** — `PostClosingFeedbackModal` that auto-fires on first view of a recently-closed transaction.

All ten pillars are bounded — they do not redesign Active Transactions, change the wizard, introduce a second AI provider, or replace the existing SettingsPage / Admin pages. They extend.

A critical lesson from the M4.3 / M5.1 / M5.2 retrospectives is baked into every workstream:

> **Every deliverable must be testable end-to-end through the frontend UI by a non-developer real-estate professional.** No "backend exists but no UI to invoke it" gaps. Every `POST /api/v1/...` endpoint has a button that calls it; every list endpoint has a screen that renders it; every preference has a toggle. The acceptance criteria in §12 are written as click-paths a tester can execute without ever opening a terminal or reading code.

---

## 2. Scope

### 2.1 In scope — `milestones.txt` §5.3 deliverables (v2.0 surface placement)

| # | Milestone deliverable | Surface category | Visible route(s) | Workstream |
| --- | --- | --- | --- | --- |
| 1 | Brokerage profile (all agents/teams in one dashboard) | **Admin** | `/admin/brokerage` (NEW) | §5.A · §6.A |
| 2a | Agent/team profile — identity | **Profile Modal** | `ProfileModal` from topbar avatar menu (NEW, shared across roles) | §5.B · §6.B |
| 2b | Agent/team profile — Internal document center (utility companies by county, etc.) | **Settings** + **Admin** | `/settings#my-internal-resources` (personal) + `/admin/team-internal-resources` (team) | §5.C · §6.C |
| 2c | Agent/team profile — Preferred vendors management | **Settings** + **Admin** | `/settings#my-preferred-vendors` (personal) + `/admin/team-vendors` (team) | §5.C · §6.C |
| 2d | Agent/team profile — Buyer and Seller closing checklist templates | **Settings** + **Admin** | `/settings#my-checklist-templates` (personal) + `/admin/team-checklist-templates` (team) | §5.C · §6.C |
| 2e | Agent/team profile — Tagged note management for checklist printing | **Settings** + **Admin** | `/settings#my-tagged-notes` (personal) + `/admin/team-tagged-notes` (team) | §5.C · §6.C |
| 2f | Agent/team profile — Seller escrow-overage reminder defaults | **Settings** | Inside `/settings#my-checklist-templates` (it's a sub-field of the seller template) | §5.C · §6.C |
| 2g | Agent/team profile — Closed transaction reminders (tax exemptions, reviews) | **Settings** | Inside `/settings#notifications` as a sub-card | §5.C · §6.C |
| 2h | Agent/team profile — Notification preferences (on/off) | **Settings** | `/settings#notifications` (NEW section) | §5.C · §6.C |
| 3a | Client portal — Milestone sharing | **Client Settings** | `/client/settings` (NEW) Milestone Sharing Defaults card | §5.D · §6.D |
| 3b | Client portal — Agent BIO / Learn About Your Agent | **Client Settings** (read-only card) + `/client/agent` (existing, lightly extended) | `/client/settings` Agent BIO card + `/client/agent` | §5.D · §6.D |
| 3c | Client portal — Notification preferences | **Client Settings** | `/client/settings` Notifications card | §5.D · §6.D |
| 3d | Client portal — Identity edits | **Profile Modal** | Shared `ProfileModal` from Client avatar menu | §5.B · §6.B |
| 4a | FSBO portal — Notification preferences management | **FSBO Settings** | `/fsbo/settings` (NEW) Notifications card | §5.E · §6.E |
| 4b | FSBO portal — Milestone sharing preferences (link expiry, viewer alerts) | **FSBO Settings** | `/fsbo/settings` Milestone Sharing Defaults card | §5.E · §6.E |
| 4c | FSBO portal — Support/guide contact preferences | **FSBO Settings** | `/fsbo/settings` Support Contact card | §5.E · §6.E |
| 4d | FSBO portal — Identity edits | **Profile Modal** | Shared `ProfileModal` from FSBO avatar menu | §5.B · §6.B |
| 5 | AI closing checklist generator (Agent sheet + Client sheet; standard data per agent/team; dates, utility info, address change guides; print sourced from profile templates) | Feature (cross-cutting) | `PrintChecklistModal` invoked from Print Checklist buttons on Solo Agent dashboard, Team Leader dashboard, Active Transactions expanded card footer, Transaction Detail, and Settings → My Checklist Templates "Preview" | §5.F · §6.F |
| 6 | Natural-language task creation (AI converts plain language to structured task objects; due date + reminder rule generation) | Feature (cross-cutting) | `AiNlpTaskModal` invoked from "✦ Quick add" on Active Transactions drawer and `/tasks/queue` | §5.G · §6.G |
| 7 | Dynamic task intelligence UI (AI recommendations with reasons/sources; Approve/restore controls; Bulk approval for team leads with preview) | Feature (cross-cutting) | `/ai-suggestions` (page rebuild — already in the Intelligence sidebar group) + AI Suggestions strip in Active Transactions expanded drawer + Team-Lead Bulk Accept preview modal | §5.H · §6.H |
| 8 | Task feedback loop UI (post-closing: useful/unnecessary/missing) | Feature (cross-cutting) | `PostClosingFeedbackModal` auto-fires on first view of a recently-closed transaction; also reachable from the Closed-transactions list and the Transaction History panel | §5.I · §6.I |

**Surface count summary:** 1 admin landing extension (`/admin/brokerage`) + 4 admin team-config pages + 5 new Settings sections + 2 new portal Settings pages (`/client/settings`, `/fsbo/settings`) + 1 shared `ProfileModal` (replaces three would-be Profile pages — internal, Client, FSBO) + 4 cross-cutting feature surfaces (PrintChecklistModal, AiNlpTaskModal, AISuggestionsPage rebuild, PostClosingFeedbackModal). The Profile surface is a modal — no route, no tabs. The M5.1 Reports tab folds into `/analytics`.

### 2.2 Explicitly excluded (do **not** scope-creep)

- **White-label brand configuration UI** (logo upload, primary/secondary color editor, custom domain). Branding tile in Settings stays a placeholder until M6.1.
- **Brokerage page as a CRUD surface.** Adding/removing agents continues to use `/admin/users` (M1.3).
- **A second AI provider, embeddings, vector search, RAG, or any new LLM infrastructure.** NLP parsing and suggestion generation reuse the existing `app/services/ai_service.py` via the existing provider abstraction.
- **Replacing the existing SettingsPage shell.** We *append* sections to the same scrolling-document pattern; we do not refactor the sticky left-rail nav or the Section interaction model.
- **Replacing the existing admin section's information architecture.** The new admin pages append; they don't reorganize the existing `/admin/users`, `/admin/task-templates`, `/admin/communications`, `/admin/audit-logs`, `/admin/confidence`, `/admin/tenant`, `/admin/payment-access`, `/admin/vendor-templates` set.
- **A new contacts/vendors directory.** Preferred Vendors lists are ordered `vendor_id` shortlists referring to the existing `vendors` table.
- **Multi-tenant data migrations.** All schema changes are additive — one new table (`ai_suggestions`), one new table (`ai_suggestion_feedback`), and JSONB schema *conventions* on existing `users.profile_settings_json` and `teams.settings_json`.
- **Predictive analytics, AI Coach, AI custom video creator.** Post-MVP roadmap.
- **Major refactor of the M5.1 `/analytics` page.** The Reports tab folds in as a per-user view; `/analytics` itself already supports `?agent_id=me` scoping. The migration is a small cleanup ticket — move the tab content, redirect `/profile?tab=reports` → `/analytics?scope=me`, delete the tab — no `/analytics` rebuild.

### 2.3 Boundary with adjacent milestones

| Provides upstream of M5.3 | Already shipped in |
| --- | --- |
| `users.profile_settings_json` JSONB column | M1.2 — empty by default; M5.3 defines a schema convention |
| `users.notification_prefs` JSONB column + read in `task_notification_service.py` | M1.2 + M2.2 + M4.1 |
| `teams.settings_json` JSONB column | M1.3 |
| Profile shell (`UserProfilePage` with Personal Info + Reports tabs) | M5.1 |
| `SettingsPage` seven-section scrolling document | M4.1 + M5.2 |
| Admin section shell (`AdminPageHeader`, list/detail patterns) | M1.3 + M5.1 + M5.2 |
| `closing_checklist.py` service returning task-list shape | M2.4 |
| AI provider abstraction (`app/services/providers/`, `app/services/ai_service.py`) | M3.1 |
| `vendors` table + `/api/v1/vendors` CRUD + opt-in vendor contact cards | M4.3 |
| Notification UI shell + `usePendingNotifications` | M4.1 + M5.1 |
| Tour provider + Settings → Help & Tour replay flow | M2.3 + M5.1 |
| Existing `/ai/recommend-tasks` and `/ai/suggest-task-approach` AI endpoints (stateless) | M3.1 |
| Active Transactions expanded drawer with AI Suggestions panel placeholder | M2.4 / `FRONTEND_UI_WORKFLOW_LOGIC.md` §4.1 |
| `/analytics` page (per-agent / team / tenant analytics) | M5.1 |

| Consumed downstream of M5.3 | Owned by |
| --- | --- |
| White-label brand colors applied to printed checklists | M6.1 |
| AI Coach add-on consuming `ai_suggestions` + feedback corpus | Post-MVP |
| QuickBooks/Xero adapter consuming closed-transaction tax-exemption reminders | Post-MVP |
| Full security + accessibility audit covering new surfaces | M7.1 |

---

## 3. Foundation Audit — Current State vs. What We Add

### 3.1 Backend — Current state

| File / surface | What's there today | What M5.3 adds |
| --- | --- | --- |
| `app/models/user.py` | `profile_settings_json: dict` and `notification_prefs: dict` JSONB fields, both default-empty. No code reads them for checklist templates / preferred vendors yet. | No new columns. M5.3 defines a **schema convention** documented in the model docstring: `profile_settings_json` carries five top-level keys — `agent_bio` (string, surfaced on Client/FSBO Agent BIO cards), `closed_transaction_reminders` (list of reminder rule objects), `milestone_sharing_defaults` (object — client/FSBO only), `user_checklist_templates` (object: `{ buyer_template, seller_template }`), `user_tagged_notes` (array of tagged-note rows). Preferred vendors and internal resources are NOT in this JSONB — they live in dedicated tables (`user_preferred_vendors` join + `documents` rows with `document_type='internal_resource'`) for clean FK semantics and storage-bucket scoping. |
| `app/repositories/user_repository.py` | Reads/writes both JSONB fields. | Add `update_profile_settings(user_id, partial_dict)` helper that deep-merges into `profile_settings_json`. Convention: the helper accepts only whitelisted top-level keys (`agent_bio`, `closed_transaction_reminders`, `milestone_sharing_defaults`, `user_checklist_templates`, `user_tagged_notes`); anything else returns 400. Other personal preferences live outside this JSONB: preferred vendors in the `user_preferred_vendors` join table, internal resources in the `documents` table (both per §5.J). |
| `app/models/team.py` | `settings_json: dict` exists. | M5.3 schema convention for `settings_json` keys edited via the new admin pages: `team_buyer_checklist_template`, `team_seller_checklist_template`, `team_tagged_notes[]`, `team_preferred_vendor_ids[]`, `team_internal_resource_document_ids[]`. Inheritance: at composition time (e.g., the closing checklist service or the preferred vendors service), if the user's value is missing the team's value is used; this happens **server-side**, transparent to the UI. |
| `app/services/closing_checklist.py` | Returns a flat task-list shape. Docstring already notes profile-template-driven content is a "Slice 4 enhancement" deferred to a future milestone (us). | Add a `template_source` field on the response and a new `build_two_sheet_checklist(...)` function that composes Agent Sheet + Client Sheet. Sources from `user.profile_settings_json` first; falls back to `team.settings_json`; falls back to `tenants.settings_json['default_checklist_templates']` if both empty. The existing task-list shape stays the default for back-compat. |
| `app/api/v1/tasks.py` | Has CRUD, completion, similarity check (M2.2). | Add `POST /api/v1/tasks/parse-nl` returning a structured task draft. Does NOT save; the frontend posts the user-confirmed payload to `POST /api/v1/tasks`. |
| `app/api/v1/ai.py` | Has `/recommend-tasks` and `/suggest-task-approach` — **stateless** today. | Add a persistent suggestion store. Add `GET /api/v1/ai/suggestions`, `GET /api/v1/ai/suggestions/stats`, `POST /api/v1/ai/suggestions/{id}/accept`, `POST /api/v1/ai/suggestions/{id}/dismiss` per `SYSTEM_DESIGN.md` §3.2. |
| `app/services/ai_service.py` | Wraps the provider abstraction. | Add `parse_natural_language_task(text, tx_context)`. Add `record_task_feedback(transaction_id, task_id, verdict, note)` that appends to a per-tenant feedback corpus capped at 500 entries (FIFO). |
| `app/services/notification_prefs_service.py` (NEW) | Does not exist. `task_notification_service.py` reads `notification_prefs` ad-hoc today. | New small service that owns the **shape** of `notification_prefs`: a 2D matrix of `{category: {channel: bool}}`. Categories: `task_assignment, task_due, document_action, ai_email_sent, communications_received, deadline_reminder, daily_summary, milestone_share_viewed, closed_transaction_reminder`. Channels: `email, push, in_app`. Exposes `get_prefs(user)`, `update_prefs(user, partial)`, and `should_notify(user, category, channel)`. |
| `app/services/preferred_vendors_service.py` (NEW) | Does not exist. | Resolves a user's preferred vendor shortlist to hydrated `Vendor` records. Composition order: user list (from `user_preferred_vendors` join table — see §5.J) → team list (from `teams.settings_json['team_preferred_vendor_ids']`) → empty. |
| `app/services/internal_resources_service.py` (NEW) | Does not exist. The `app/api/v1/documents.py` file has an `_is_internal_document_user(...)` helper but no surface for profile-resource lookup. | Thin wrapper that lists documents flagged `document_type='internal_resource'` AND `transaction_id IS NULL`, scoped by `created_by_user_id = me` OR `team_owned_internal_resource_ids` (a list on the team's `settings_json`). Tagged with optional `category` ('utility_companies', 'county_resources', 'address_change_guide', 'closing_guide', 'other'). |
| `app/services/closed_transaction_reminder_service.py` (NEW) | Does not exist. | Cron-driven daily job that fires reminders per `user.profile_settings_json['closed_transaction_reminders']`. Uses `notification_prefs_service.should_notify(...)`. Manual trigger: `POST /api/v1/admin/run-closed-tx-reminders` for QA. |
| `app/api/v1/brokerage.py` (NEW under `/admin/brokerage` route group) | Does not exist. | Two endpoints: `GET /api/v1/admin/brokerage/overview` and `GET /api/v1/admin/brokerage/teams/{team_id}/agents`. Gated TL+Admin. |
| `app/api/v1/admin_team_templates.py` (NEW) | Does not exist. | `GET / PUT /api/v1/admin/team-checklist-templates`, `GET / PUT /api/v1/admin/team-tagged-notes`, `GET / PUT /api/v1/admin/team-preferred-vendors`, `GET / PUT / POST / DELETE /api/v1/admin/team-internal-resources`. All gated TL+Admin (TL scoped to own team; Admin tenant-wide). Each is a thin handler over `teams.settings_json` and the `documents` table. |
| `app/api/v1/client_settings.py` and `app/api/v1/fsbo_settings.py` (NEW) | Do not exist. The current `/client/agent` returns agent info but no client-self-preferences surface exists. | `GET / PUT /api/v1/client/settings` (notification prefs + sharing defaults + agent BIO read-through) and the FSBO mirror. |
| `supabase/migrations/*` | Latest existing migration: `20260726090000_milestone_5_2_payments.sql` (assumed). | One new migration: `20260802090000_milestone_5_3_personalization.sql`. Tables: `ai_suggestions`, `ai_suggestion_feedback`, `user_preferred_vendors` (join). One new `documents.category` text column (nullable; only set when `document_type='internal_resource'`). |
| `app/services/audit_service.py` | Existing. | Audit every Settings save, every Admin team-config save, every AI suggestion accept/dismiss, every NLP task confirmation, every feedback submission. |
| `app/services/dashboard_aggregator.py` | M5.1 / M5.2. | Add `brokerage_overview(tenant)` returning aggregated stats for `/admin/brokerage`. |

### 3.2 Frontend — Current state

| File / surface | What's there today | What M5.3 adds |
| --- | --- | --- |
| `src/pages/users/UserProfilePage.tsx` | Two tabs: Personal info + Reports (the latter from M5.1). | **Delete.** Replaced by `ProfileModal` for identity edits and the existing `/analytics` page for Reports. The `/profile` route is deleted (301-redirected to `/analytics?scope=me` for any bookmarks). `/client/profile` and `/fsbo/profile` — proposed in v2.0 — are never added; portal users open the shared `ProfileModal` from their avatar menus. |
| `src/components/profile/ProfileModal.tsx` (NEW) | Does not exist. | Net-new shared modal. ~480 px wide. Renders a single identity card with: avatar uploader (Supabase Storage `user-avatars` bucket), full_name, email (read-only), phone, bio (textarea, 1000 char), company_name. Save calls `PATCH /api/v1/users/me`. Used by **every role** (internal, Client, FSBO) — opened from each role's topbar avatar menu. No role-specific variants — capability differences (Client/FSBO can't edit company_name) are gated inside the modal via `useAuth().user.role`. |
| `src/components/users/UserForm.tsx` | Edits `full_name` and `phone`. | **Refactor into `ProfileModal`'s body.** The existing UserForm logic moves into the modal; the old `UserProfilePage` host is deleted. PATCH endpoint and field set are extended (bio, company_name, avatar_url). |
| `src/pages/settings/SettingsPage.tsx` | Eight sections + sticky left-rail nav (Company / Email Integrations / E-Signature / Branding / AI Configuration / Task Templates / Help & Tour / Danger Zone). | **Append five new sections** at logical positions in the sticky nav. Sort: Company → **Notifications (NEW)** → Email Integrations → E-Signature → **My Closing Checklist Templates (NEW)** → **My Tagged Notes (NEW)** → **My Preferred Vendors (NEW)** → **My Internal Resources (NEW)** → Branding → AI Configuration → Task Templates → Help & Tour → Danger Zone. Thirteen sections total. Same scrolling-document pattern. |
| `src/components/profile/print/` (empty) | Empty. | Net-new: `PrintChecklistModal.tsx`. |
| `src/components/profile/templates/` (empty) | Empty. | Net-new: `BuyerChecklistTemplateEditor.tsx`, `SellerChecklistTemplateEditor.tsx`, `TaggedNotesEditor.tsx`, `PreferredVendorsPicker.tsx`. These are **shared components** used by both `/settings#my-*` sections AND `/admin/team-*` pages (same editor, different storage target). |
| `src/components/profile/resources/` (empty) | Empty. | Net-new: `InternalResourcesPanel.tsx`. Shared by `/settings#my-internal-resources` AND `/admin/team-internal-resources`. |
| `src/components/profile/notifications/` (NEW) | Does not exist. | Net-new: `NotificationPrefsMatrix.tsx`, `ClosedTxReminderEditor.tsx`. Used by `/settings#notifications`, `/client/settings`, `/fsbo/settings`. |
| `src/pages/profile/` (empty) | Empty. | **Delete the directory.** No Profile page lives anywhere now — the ProfileModal replaces it. |
| `src/pages/AnalyticsPage.tsx` | M5.1 — per-agent / team / tenant analytics with `agent_id` scoping. | Add `?scope=me` query param shortcut + sub-nav tab "My reports" (renders the same charts filtered to `agent_id=me`). Absorbs the content of the deleted `/profile` Reports tab. |
| `src/pages/AISuggestionsPage.tsx` | `ComingSoonPage` placeholder. | Replace with the canonical Suggestions inbox per `completed_designs/ve-intelligence-ai_suggestions.html`. |
| `src/components/active-transactions/TransactionDrawer.tsx` (or equivalent inside `TransactionListPage.tsx`) | Renders 3-column drawer. The M2.4 spec calls for an AI Suggestions sub-panel below the columns. | Wire the existing hook to fetch `GET /api/v1/ai/suggestions?transaction_id={id}` (top 3). Render `AiSuggestionStrip`. Add **"✦ Quick add"** button beside the existing "+ Add Task" CTA. |
| `src/pages/tasks/TaskQueuePage.tsx` | M2.4. | Add **"✦ Quick add"** button beside the existing "+ Add Task" CTA. Same modal. |
| `src/pages/client/ClientAgentInfoPage.tsx` | Renders agent info (M5.1). | Surface `agent_bio` from the agent's `profile_settings_json`. Add `company_name` and full phone formatting. |
| `src/pages/client/ClientSettingsPage.tsx` (NEW) | Does not exist. | Net-new. Three cards: Notification Preferences, Milestone Sharing Defaults, Agent BIO (read-only). Reachable from the avatar menu Settings entry. (Identity edits use the shared `ProfileModal` from a separate avatar menu Profile entry.) |
| `src/pages/fsbo/FsboSettingsPage.tsx` (NEW) | Does not exist. | Net-new. Cards: Notification Preferences, Milestone Sharing Defaults, Support / Guide Contact Preferences, FSBO Boundary Notice. (Identity edits use the shared `ProfileModal`.) |
| `src/pages/admin/AdminBrokerageOverviewPage.tsx` (NEW) | Does not exist. | Net-new. Sits inside the existing admin section with `AdminPageHeader` breadcrumb (Admin › Brokerage Overview). KPI strip + agent table + teams rail. |
| `src/pages/admin/AdminTeamChecklistTemplatesPage.tsx` (NEW) | Does not exist. | Net-new. Two-column editor reusing the same Buyer/Seller template editors that ship under Settings. Saves to `teams.settings_json`. |
| `src/pages/admin/AdminTeamTaggedNotesPage.tsx` (NEW) | Does not exist. | Net-new. Reuses `TaggedNotesEditor`. Saves to `teams.settings_json['team_tagged_notes']`. |
| `src/pages/admin/AdminTeamVendorsPage.tsx` (NEW) | Does not exist. | Net-new. Reuses `PreferredVendorsPicker`. Saves to `teams.settings_json['team_preferred_vendor_ids']`. |
| `src/pages/admin/AdminTeamInternalResourcesPage.tsx` (NEW) | Does not exist. | Net-new. Reuses `InternalResourcesPanel`. Saves to `teams.settings_json['team_internal_resource_document_ids']` and writes `document_type='internal_resource'` rows owned by the team. |
| `src/components/active-transactions/PostClosingFeedbackModal.tsx` (NEW) | Does not exist. | Net-new. Auto-fires on first view of a tx whose `completed_at` is within last 7 d AND no row in `ai_suggestion_feedback` for this user × tx. |
| `src/components/tasks/AiNlpTaskModal.tsx` (NEW) | Does not exist. | Net-new. Two-step modal: NL textarea → review parsed payload → save. |
| `src/components/ai-suggestions/AiSuggestionCard.tsx` (NEW) | Does not exist. | Net-new. Card per `completed_designs/ve-intelligence-ai_suggestions.html` anatomy. |
| `src/components/ai-suggestions/AiSuggestionStrip.tsx` (NEW) | Does not exist. | Net-new. Top-3 strip inside the Active Tx drawer. |
| `src/components/ai-suggestions/BulkAcceptPreviewModal.tsx` (NEW) | Does not exist. | Net-new. TL-only Bulk Accept preview. |
| `src/components/dashboard/PrintChecklistButton.tsx` (likely inline in dashboards + card footers) | The existing Print Checklist deep-link fires `GET /api/v1/transactions/:id/checklist` and renders the response in `window.print()`. | Update to open the new `PrintChecklistModal` instead. Graceful fallback if no profile templates set. |
| `src/utils/constants.ts` (ROUTES) | All existing routes. | Add `ADMIN_BROKERAGE`, `ADMIN_TEAM_CHECKLIST_TEMPLATES`, `ADMIN_TEAM_TAGGED_NOTES`, `ADMIN_TEAM_VENDORS`, `ADMIN_TEAM_INTERNAL_RESOURCES`, `CLIENT_SETTINGS`, `FSBO_SETTINGS`. **Remove** `PROFILE` from the constants (route deleted). No `CLIENT_PROFILE` or `FSBO_PROFILE` constants — Profile is a modal. |
| `src/App.tsx` | Route table. | Add the seven new routes. Gate the five admin routes (Admin; TL allowed on team-scoped pages). **Delete** the `/profile` route + add a 301 redirect to `/analytics?scope=me` for back-compat. |
| `src/layouts/AppLayout.tsx` sidebar grouping | Existing groups: Dashboard, Deals, Workflow, Intelligence, Team. | Add Brokerage Overview + four team-config pages inside the **Admin** menu, NOT under Team. **Avatar menu update:** every role gets explicit "Profile" + "Settings" + "Sign out" entries. "Profile" opens `ProfileModal` (does not navigate); "Settings" navigates to the role's Settings route (`/settings`, `/client/settings`, `/fsbo/settings`). |
| `src/contexts/ProfileModalContext.tsx` (NEW) | Does not exist. | Net-new. Provides `useProfileModal()` hook with `open()` / `close()`. Mounted once at app root (same pattern as `FsboShareContext` from M5.1). The single mount means any component (avatar menu in any role's layout) can call `useProfileModal().open()` without local state. |

### 3.3 Reusable design fragments

- **Profile (`ProfileModal`):** Refactor the existing `UserForm.tsx` field/validation logic into the modal body; host inside the shared Radix `<Dialog>` primitive (per `STYLE_GUIDE.md §6.5`). The old `UserProfilePage.tsx` host and its `ProfileCard.tsx` read-only summary are deleted with the route.
- **Settings new sections:** Reuse the existing `SettingsPage` section pattern (label · description · input · save). Sticky left-rail nav grows from 8 items to 13.
- **Notifications matrix:** `<Switch>` + label row pattern from existing AI Configuration card; 2D grid `grid-cols-[1fr_repeat(3,auto)] gap-3` with sticky header.
- **Checklist editors:** Use shadcn `<Textarea>` with markdown-light syntax (bold / italic / bullet list only — no WYSIWYG). Section-bound editor: "Closing expectations" / "Utility transfer guide" / "Address change guide" / (seller only) "Escrow overage reminder".
- **Preferred vendors picker:** Typeahead over `/api/v1/vendors` with drag-handle reorder and keyboard `↑/↓` shortcuts.
- **Internal resources panel:** Reuse existing document upload component with `transaction_id=null` and a `category` dropdown.
- **AI Suggestions page:** Mirror `completed_designs/ve-intelligence-ai_suggestions.html`. Confidence ring uses existing `HealthScoreRing` shared component.
- **NLP task modal:** Two-step form pattern matching existing Quick-Create Transaction modal (M2.4).
- **Print checklist modal:** Two `<section data-print-sheet="agent">` / `<section data-print-sheet="client">` blocks with `@media print` CSS.
- **Admin team-config pages:** Reuse `AdminPageHeader` (per `STYLE_GUIDE.md §15.2`). One card per page; same editor components used in Settings.
- **Brokerage Overview:** Reuse `DashboardKpiCard` + `MainRailGrid` (M5.1). Agent table reuses M1.3 `AdminUsersListPage` row anatomy.

### 3.4 What the audit revealed that prior plans missed

- **The Profile page only edits two fields today.** Don't over-extend it — and given how slim it is, don't even keep it as a page. v2.1 converts it to a modal.
- **The M5.1 Reports tab on `/profile` duplicates `/analytics`.** Same data, two routes. Fold it back into `/analytics` with a `?scope=me` shortcut and a "My reports" sub-nav tab.
- **The Settings page is already the natural home for personal preferences** and has a scrolling-document pattern that scales to ~12 sections without restructuring.
- **The Admin section already has a consistent pattern** (`AdminPageHeader`, breadcrumb-style header) — the new admin pages slot in cleanly.
- **AI suggestions have no persistent table.** Without persistence the "AI Suggestions inbox" cannot exist. M5.3 adds the `ai_suggestions` table and writes to it from explicit `recommend-tasks` calls (the user clicks "Recommend tasks for this deal" on the Active Tx drawer). A future background generator that produces suggestions automatically on state changes is **post-MVP** — see §11 risk #6. The explicit-button approach satisfies the M5.3 deliverable.
- **Client/FSBO portals have no settings page today.** `/client/agent` exists but is the **agent's** info, not the client's preferences.
- **The closing checklist generator is a backend-only endpoint without a useful UI.** The existing `/api/v1/transactions/:id/checklist` returns a flat task list with no per-tenant customization.
- **Components/profile/{print,resources,templates}/ directories are empty.** Someone scoped them earlier without building them; M5.3 closes them out.

---

## 4. Architecture Overview

### 4.1 Data flow per pillar

```
┌─ Settings save (Notifications / Templates / Vendors / Resources / Closed-Tx Reminders) ─┐
│                                                                                          │
│   SettingsPage section save                                                              │
│       │                                                                                  │
│       ▼                                                                                  │
│   Per-section endpoint:                                                                  │
│     PATCH /api/v1/users/me  (for profile_settings_json keys)                             │
│     PUT   /api/v1/notifications/preferences                                              │
│     PUT   /api/v1/users/me/preferred-vendors                                             │
│     PUT/POST/DELETE /api/v1/users/me/internal-resources                                  │
│     PUT   /api/v1/users/me/checklist-templates                                           │
│       │                                                                                  │
│       ▼                                                                                  │
│   Deep-merge into JSONB (whitelisted keys only) + AuditService.log                       │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘

┌─ Admin team-config save ────────────────────────────────────────────────────────────────┐
│                                                                                          │
│   AdminTeamX page save                                                                   │
│       │                                                                                  │
│       ▼                                                                                  │
│   PUT /api/v1/admin/team-{checklist-templates|tagged-notes|preferred-vendors|            │
│        internal-resources} (TL scoped to own team; Admin scoped to any tenant team)      │
│       │                                                                                  │
│       ▼                                                                                  │
│   Deep-merge into teams.settings_json + AuditService.log                                 │
│   (audit summary: "Team Lead X edited Team Buyer Checklist Template")                    │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘

┌─ Closing checklist composition (server-side inheritance) ───────────────────────────────┐
│                                                                                          │
│   GET /api/v1/transactions/{id}/checklist?format=two_sheet                               │
│       │                                                                                  │
│       ▼                                                                                  │
│   closing_checklist.build_two_sheet_checklist(tx, user)                                  │
│     for each section the agent sheet / client sheet requires:                            │
│       value = user.profile_settings_json[key]                                            │
│       if value is empty: value = team.settings_json[team_key]                            │
│       if still empty: value = tenants.settings_json[default_key]                         │
│       template_source ∈ {user, team, tenant_default}                                     │
│       │                                                                                  │
│       ▼                                                                                  │
│   PrintChecklistModal renders both sheets with a caption                                 │
│   "Source: your personal template / your team's template / system default"               │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘

(NLP task creation, AI Suggestions, Post-closing feedback flows — unchanged from v1.0
 — see prior §4.1 diagrams.)
```

### 4.2 Permissions (extends the M5.1 + M5.2 matrix)

| Action | Default allowed roles | Notes |
| --- | --- | --- |
| View own Profile (identity) | All authenticated | `ProfileModal` opened from topbar avatar menu (no route) |
| Edit own Profile (identity) | All authenticated | name, phone, bio, company_name (hidden for Client/FSBO/Vendor), avatar_url |
| View own Settings (personal preferences) | All authenticated | `/settings`, `/client/settings`, `/fsbo/settings` per role |
| Edit own Settings (personal preferences) | All authenticated | All five new sections + the existing seven |
| View Brokerage Overview (`/admin/brokerage`) | Team Lead, Admin | Hidden from Agent / TC / Attorney / Client / FSBO / Vendor sidebar |
| Edit Team Checklist Templates (`/admin/team-checklist-templates`) | Team Lead (own team), Admin (any team) | TL gets a team selector defaulting to their own team |
| Edit Team Tagged Notes | Team Lead, Admin | Same scoping |
| Edit Team Preferred Vendors | Team Lead, Admin | Same scoping |
| Edit Team Internal Resources | Team Lead, Admin | Same scoping |
| Create AI suggestions | System (auto) + explicit Recommend buttons (Agent/TC/TL) | The generator is system-owned; only humans accept/dismiss |
| Accept AI suggestion `scope='transaction'` | Agent (own tx), TC (assigned tx), Team Lead (any team tx), Admin, Attorney (attorney-relevant only) | Per `requirements.txt` §4.4 |
| Accept AI suggestion `scope='all_future'` | Team Lead (with preview), Admin | Bulk approval preview required |
| Submit post-closing feedback | Agent, TC, Team Lead | Once per user-per-transaction |
| Parse NLP task | Agent, TC, Team Lead | Behind `requires_role` |
| Edit client Settings (`/client/settings`) | Client | Self only |
| Edit FSBO Settings (`/fsbo/settings`) | ForSaleByOwner | Self only |

### 4.3 AI-vs-human guardrails

Unchanged from v1.0 — NLP parsing and suggestion generation are AI-prepared, not AI-decided. Every output editable; nothing saves without an explicit human click. Per-field confidence chips on the NLP modal step 2. Compliance tasks can't be removed by an Accept on a remove-task suggestion. Attorney guardrail preserved on attorney-owned matters.

### 4.4 White-label readiness

Unchanged from v1.0 — all new components use `ve-*` tokens; printed checklist uses tenant CSS variables; Brokerage Overview header uses `useCurrentTenant()`; Client portal Agent BIO uses the agent's company logo.

---

## 5. Workstream A — Backend

### 5.A Brokerage Overview — `app/api/v1/admin_brokerage.py` (NEW under admin router)

| Endpoint | Returns | Notes |
| --- | --- | --- |
| `GET /api/v1/admin/brokerage/overview` | `{ tenant: {name, slug, logo_url, agent_count, team_count, active_transaction_count, pipeline_volume_cents, closing_this_week_count}, agents: [...], teams: [...] }` | Composition of existing aggregator calls. |
| `GET /api/v1/admin/brokerage/teams/{team_id}/agents` | List of agents in a team with per-agent pipeline | Team-row drill-down. |

Gated `requires_role('TeamLead','Admin')`. No mutations — CRUD remains at `/admin/users`.

### 5.B Profile (identity) — extend `app/api/v1/users.py`

```
PATCH /api/v1/users/me
  body: { full_name?, phone?, bio?, company_name?, avatar_url?,
          profile_settings?: { whitelisted partial deep-merge —
                               allowed keys: agent_bio,
                               closed_transaction_reminders,
                               milestone_sharing_defaults,
                               user_checklist_templates,
                               user_tagged_notes } }
```

Implementation:

```python
ALLOWED_PROFILE_SETTINGS_KEYS = {
  'agent_bio',
  'closed_transaction_reminders',
  'milestone_sharing_defaults',
  'user_checklist_templates',
  'user_tagged_notes',
}

async def update_profile_settings(self, user_id: str, partial: dict) -> User:
    unknown = set(partial) - ALLOWED_PROFILE_SETTINGS_KEYS
    if unknown:
        raise PermissionError(f"Unknown profile_settings keys: {unknown}")
    current = await self.get_by_id(user_id)
    merged = _deep_merge(current.profile_settings_json, partial)
    # save merged; audit_service.log diff between current and merged.
```

The ProfileModal in practice only sends `full_name`, `phone`, `bio`, `company_name`, `avatar_url` + `profile_settings: { agent_bio }` — it does not write checklist templates or tagged notes. Those have their own dedicated endpoints (§5.C) for narrower per-call validation and clearer audit summaries (`user_checklist_templates_update` instead of generic `profile_update`). All endpoints share `update_profile_settings` under the hood, which is why the whitelist covers all five keys. Preferred vendors and internal resources do **not** route through this helper at all — they live in dedicated tables.

### 5.C Settings (personal preferences) — five new endpoint groups

**Notifications** (extends `app/api/v1/notifications.py`):

```
GET /api/v1/notifications/preferences  →  current matrix
PUT /api/v1/notifications/preferences  →  partial update (deep-merge)
```

**My Closing Checklist Templates** (NEW `app/api/v1/my_checklist_templates.py`):

```
GET /api/v1/me/checklist-templates   →  { buyer_template, seller_template,
                                          team_buyer_template (read-only inherit view),
                                          team_seller_template (read-only inherit view) }
PUT /api/v1/me/checklist-templates   →  body: { buyer_template?, seller_template? }
                                        (saves into user.profile_settings_json under
                                         user_checklist_templates key — separate
                                         JSONB sub-object so it's editable independently)
```

Storage convention: `user_checklist_templates` is a top-level key in `profile_settings_json` (whitelisted in §5.B). This endpoint is the canonical write path because it carries narrower validation (only `buyer_template` and `seller_template` sub-keys accepted) and produces a more specific audit entry (`user_checklist_templates_update`) than the generic `PATCH /users/me`.

**My Tagged Notes** (NEW `app/api/v1/my_tagged_notes.py`):

```
GET /api/v1/me/tagged-notes  →  { user_tagged_notes: [...], team_tagged_notes: [...] }
PUT /api/v1/me/tagged-notes  →  body: { user_tagged_notes: [...] }   (full replacement)
```

**My Preferred Vendors** (NEW `app/api/v1/my_preferred_vendors.py`):

```
GET /api/v1/me/preferred-vendors  →  hydrated [Vendor] (user list resolved + team list resolved)
PUT /api/v1/me/preferred-vendors  →  body: { vendor_ids: [uuid] }   (full replacement, ordered)
```

Storage: a dedicated join table `user_preferred_vendors(user_id, vendor_id, sort_order)` — not JSONB, because we want a clean FK to vendors so vendor deletes don't leave dangling IDs.

**My Internal Resources** (NEW `app/api/v1/my_internal_resources.py`):

```
GET    /api/v1/me/internal-resources             →  [Document]   (user list + team list)
POST   /api/v1/me/internal-resources             →  multipart upload (file + category + display_name)
DELETE /api/v1/me/internal-resources/{document_id}
```

Storage: rows in the existing `documents` table with `document_type='internal_resource'`, `transaction_id=NULL`, `category=<one of utility_companies|county_resources|address_change_guide|closing_guide|other>`. New `documents.category` nullable text column added in the M5.3 migration.

### 5.D Admin Team Configuration — `app/api/v1/admin_team.py` (NEW)

```
GET / PUT /api/v1/admin/team-checklist-templates           # ?team_id=<uuid>
GET / PUT /api/v1/admin/team-tagged-notes
GET / PUT /api/v1/admin/team-preferred-vendors
GET /        /api/v1/admin/team-internal-resources
POST  /api/v1/admin/team-internal-resources                # upload
DELETE /api/v1/admin/team-internal-resources/{document_id}
```

All gated `requires_role('TeamLead','Admin')`. TL scope: `team_id` must equal the TL's `team_id`. Admin scope: any team in the tenant. All writes audit-logged with summary `"Team Lead {name} edited Team {section} (team={team_name})"`.

Internal resources owned by a team are stored in `documents` with `created_by_user_id=<TL>`, `team_owned=true` (new boolean column added in the migration), `document_type='internal_resource'`, `transaction_id=NULL`. The `team_owned=true` flag is what `preferred_vendors_service` and `internal_resources_service` look at when composing the "team list" returned to members.

### 5.E Client / FSBO portal endpoints (NEW)

```
GET / PUT /api/v1/client/settings   →  notification_prefs + milestone_sharing_defaults
GET       /api/v1/client/agent-info →  existing M5.1 (extended to include agent_bio,
                                       company_name)

GET / PUT /api/v1/fsbo/settings     →  notification_prefs + milestone_sharing_defaults +
                                       support_guide_contact_preferences
```

### 5.F Closing Checklist Generator — extend `app/services/closing_checklist.py`

Add `build_two_sheet_checklist`. Composition rules (Agent Sheet) — sourced from user.profile_settings_json with team and tenant fallbacks per §4.1:

1. **Header** — `tx.address`, `tx.closing_date`, primary parties summary, agent's company name from profile.
2. **Tasks** — derived from current task list grouped by status. Existing v1 service behavior.
3. **Utility Companies** — documents from `internal_resources` filtered by `category='utility_companies'`.
4. **Closing Expectations** — from `user_checklist_templates.buyer_template.closing_expectations` (or seller_template depending on representation).
5. **Tagged Notes** — from `user_tagged_notes` filtered to tags matching transaction (buyer / seller / cash / financed / fsbo / investor / owner_occupied / both / all).
6. **Seller Escrow Overage Reminder** — from `user_checklist_templates.seller_template.escrow_overage_reminder` (Seller representations only).
7. **Closed-transaction reminders preview** — upcoming scheduled reminders for this deal.

Composition rules (Client Sheet) — same fallback chain:

1. **Header** — same.
2. **Key dates** — closing, possession, utility transfer cutoff.
3. **Utility transfer guide** — from `user_checklist_templates.{buyer|seller}_template.utility_transfer_guide`.
4. **Address change guide** — from `user_checklist_templates.{buyer|seller}_template.address_change_guide`.
5. **Who to call** — party contacts.
6. **Closing reminders for the client** — escrow info, tax exemption filings, review request.

Endpoint shape:

```
GET /api/v1/transactions/{id}/checklist?format=two_sheet
  returns TwoSheetChecklistResponse with template_source per sheet

GET /api/v1/transactions/{id}/checklist            # back-compat — flat list (unchanged)
```

### 5.G Natural-Language Task Creation

Unchanged from v1.0 — `POST /api/v1/tasks/parse-nl` returning `StructuredTaskDraft`. Frontend posts user-confirmed payload to existing `POST /api/v1/tasks`. Output validation rejects non-JSON or schema-violating LLM responses.

### 5.H Dynamic Task Intelligence — `app/api/v1/ai_suggestions.py` (NEW)

Unchanged from v1.0 — endpoints: `GET /api/v1/ai/suggestions[?filters]`, `GET /api/v1/ai/suggestions/stats`, `POST /api/v1/ai/suggestions/{id}/accept` (with `scope='transaction'|'all_future'` and Team-Lead-required gate), `POST /api/v1/ai/suggestions/{id}/dismiss`. Dedup via `(tenant_id, transaction_id, dedup_hash)` unique index. 30-day `expires_at`.

### 5.I Post-Closing Feedback — `app/api/v1/ai_feedback.py` (NEW)

Unchanged from v1.0 — `POST /api/v1/ai/suggestion-feedback` writes to `ai_suggestion_feedback` and appends to the tenant feedback corpus (capped at 500). Prompt-context wiring in `ai_service` includes "unnecessary" verdicts in the system prompt of subsequent `/recommend-tasks` calls.

### 5.J Database migration — `supabase/migrations/20260802090000_milestone_5_3_personalization.sql`

Tables (all `tenant_id uuid not null`, RLS mirroring existing tables, `created_at` + `updated_at`):

| Table | Key columns |
| --- | --- |
| `ai_suggestions` | `id`, `tenant_id`, `transaction_id` (nullable), `created_by_actor`, `type`, `title`, `description`, `source`, `reason`, `suggested_action_json`, `confidence`, `status`, `accepted_by_user_id`, `accepted_at`, `dismissed_by_user_id`, `dismissed_at`, `dismiss_reason`, `dedup_hash`, `expires_at`. Unique `(tenant_id, transaction_id, dedup_hash)`. Index `(tenant_id, status, transaction_id, confidence DESC)`. |
| `ai_suggestion_feedback` | `id`, `tenant_id`, `transaction_id`, `submitted_by_user_id`, `task_verdicts_json`, `missing_tasks_text`, `general_feedback_text`, `submitted_at`. Unique `(transaction_id, submitted_by_user_id)`. |
| `user_preferred_vendors` | `tenant_id` (denormalized for RLS), `user_id`, `vendor_id`, `sort_order`, `created_at`. PK `(user_id, vendor_id)`. FK to `users` and `vendors`. RLS: `tenant_id` check + `user_id = auth.uid()` for read/write. The denormalized `tenant_id` mirrors the M5.2 payments pattern — cleaner RLS than joining through `users` on every query. |

Column additions:

- `documents.category` text NULL (only meaningful when `document_type='internal_resource'`).
- `documents.team_owned` boolean DEFAULT false NOT NULL.

No new columns on `users` or `teams` — both already have JSONB fields M5.3 layers schema-conventions on. The whitelist of allowed `profile_settings_json` keys is enforced at the service layer.

No SQL audit triggers — audit logging is at the service layer.

RLS: tenant_id check on all three new tables. `ai_suggestions` additionally restricts SELECT to users with role-appropriate access to the linked transaction. `user_preferred_vendors` additionally restricts read/write to `user_id = auth.uid()` (a user can only see and edit their own list).

Seed: none.

### 5.K Audit logging

Every M5.3 write audit-logged via `AuditService.log(...)`. Action strings:

| Action | Entity | Summary |
| --- | --- | --- |
| `profile_update` | `user` | "User <name> updated identity: <field-level diff>" |
| `notification_prefs_update` | `user` | "User <name> updated notification prefs: <diff>" |
| `user_checklist_templates_update` | `user` | "User <name> updated personal checklist templates" |
| `user_tagged_notes_update` | `user` | "User <name> updated personal tagged notes (n=X)" |
| `user_preferred_vendors_update` | `user` | "User <name> updated personal preferred vendors (n=X)" |
| `user_internal_resource_upload` | `document` | "User <name> uploaded internal resource '<display_name>' (category=X)" |
| `user_internal_resource_delete` | `document` | "User <name> deleted internal resource '<display_name>'" |
| `team_checklist_templates_update` | `team` | "Team Lead <name> updated team checklist templates (team=<team_name>)" |
| `team_tagged_notes_update` | `team` | "Team Lead <name> updated team tagged notes" |
| `team_preferred_vendors_update` | `team` | "Team Lead <name> updated team preferred vendors" |
| `team_internal_resource_upload` | `document` | "Team Lead <name> uploaded team internal resource '<display_name>'" |
| `team_internal_resource_delete` | `document` | "Team Lead <name> deleted team internal resource '<display_name>'" |
| `nl_task_parsed` | `transaction` | "AI parsed NL task from '<truncated text>' (confidence=<n>)" |
| `ai_suggestion_accept` | `ai_suggestion` | "Suggestion <type> accepted scope=<scope>" |
| `ai_suggestion_dismiss` | `ai_suggestion` | "Suggestion <type> dismissed: <reason>" |
| `ai_suggestion_feedback_submit` | `transaction` | "Post-closing feedback submitted (n_useful=X, n_unnecessary=Y)" |
| `closed_transaction_reminder_sent` | `transaction` | "Closed-transaction reminder '<rule_id>' sent to <user>" |

---

## 6. Workstream B — Frontend

### 6.A Brokerage Overview — `/admin/brokerage` (NEW)

**Route:** `/admin/brokerage` (Admin + TeamLead — non-permitted roles 404).

**Entry points:**
- Sidebar → Admin group → **"Brokerage Overview"** (NEW).
- Admin dashboard → quick-action tile **"Brokerage Overview"** (NEW).

**Layout (per `STYLE_GUIDE.md §15.2` admin page header pattern):**

```
Admin › Brokerage Overview                                             [Last refreshed: 2 min ago] [⟳]

┌─ KPI strip (DashboardKpiCard ×4) ─────────────────────────────────────┐
│ Agents │ Teams │ Active Transactions │ Pipeline Volume              │
└───────────────────────────────────────────────────────────────────────┘
┌─ Main column ─────────────────────────────┐ ┌─ Right rail ─────────┐
│ AdminCard "Agents" (sortable table:        │ │ AdminCard "Teams"     │
│   Name | Role | Team | Active Tx | Status) │ │ - Team rows w/        │
│   Each row clickable → /admin/users/:id    │ │   agent count + link  │
│                                            │ │   → /admin/users?     │
│ AdminCard "Closing this week"               │ │     team_id=          │
│ (top 5 brokerage-wide deals)               │ │                       │
└────────────────────────────────────────────┘ └───────────────────────┘
```

**Acceptance click path:**
1. Admin → sidebar **Admin → Brokerage Overview** → KPIs populated.
2. Click an agent row → land on `/admin/users/:userId`.
3. Click a team row → land on `/admin/users?team_id=<id>`.
4. Agent role → typing `/admin/brokerage` in address bar shows 404; sidebar has no Brokerage link.

### 6.B Profile Modal — `ProfileModal` (shared across all roles)

**Component:** `src/components/profile/ProfileModal.tsx`. Mounted once at app root inside `ProfileModalContext` provider. Opened via `useProfileModal().open()`.

**Entry points:** Topbar avatar menu → **"Profile"** entry (every role: internal, Client, FSBO). No URL — does not navigate, opens an overlay on whatever page the user is on.

**Layout** (per `STYLE_GUIDE.md §6.5` form-dialog primitive; reuses existing `<Dialog>` from `@/components/ui/dialog.tsx`):

```
┌─ Profile ────────────────────────────────────┐  (max-w-lg, 480px target)
│  ✦ YOUR PROFILE                              │
│                                              │
│  [Avatar circle 80×80]   [Change photo]      │
│                                              │
│  Full name *  [_____________________]        │
│  Email        [____________________ ] (read) │
│  Phone        [_____________________]        │
│  Company      [_____________________]        │  (hidden for Client/FSBO/Vendor)
│  Bio          [_____________________]        │  (textarea, 1000 char)
│                 1000 char max                │
│                                              │
│                       [Cancel]   [Save]      │
└──────────────────────────────────────────────┘
```

- Backdrop: `bg-[rgba(15,20,30,0.45)] backdrop-blur-[3px]` per `STYLE_GUIDE.md §6.5`.
- Save calls `PATCH /api/v1/users/me { full_name?, phone?, bio?, company_name?, avatar_url? }`.
- Avatar uploader uses Supabase Storage `user-avatars` bucket (M2.3); on successful upload the modal stays open and the new URL is reflected in the avatar preview.
- Escape closes; clicking outside closes (with a confirm-discard dialog if there are unsaved changes, per `STYLE_GUIDE.md §13.3` — no `window.confirm()`).
- Role gating inside the modal: `company_name` field hidden when `useAuth().user.role ∈ {Client, ForSaleByOwner, Vendor}`; bio field shown to all (Client/FSBO bios just don't surface anywhere yet but it's harmless).
- Toast on save: "Profile saved." Modal closes automatically after success.
- Mobile: full-screen modal at < 640 px; cancel/save buttons sticky-bottom.

**Reports tab migration:** The M5.1 Reports tab content moves to `/analytics`. Add a `?scope=me` query param shortcut + a "My reports" sub-nav tab on `AnalyticsPage` that pre-filters charts to `agent_id=me`. The deleted `/profile?tab=reports` URL gets a 301 redirect to `/analytics?scope=me` for any bookmarks.

**Acceptance click path:**
1. Agent → topbar avatar → **Profile** entry → modal opens over the current page (e.g., Active Transactions).
2. Edit bio "10-year Denver agent…" + add company name "Velvet Elves Realty" + click Save.
3. Modal closes; toast "Profile saved"; user is still on Active Transactions, no navigation occurred.
4. Sign in as the Client linked to this agent → `/client/agent` → new bio visible.
5. Try the same flow as Client: avatar → Profile → modal opens, Company field is NOT shown.
6. Try `/profile?tab=reports` in the address bar → 301 redirect to `/analytics?scope=me` → analytics page opens with "My reports" tab pre-selected.

### 6.C Settings extension — `/settings` (5 new sections added)

**Route:** `/settings` (existing). Sticky left-rail nav grows from 8 items to 13.

**New section order** (justifying placement):

1. Company (existing)
2. **Notifications** (NEW — high-traffic preference, place near top)
3. Email Integrations (existing — communication setup)
4. E-Signature (existing — communication setup)
5. **My Closing Checklist Templates** (NEW — content authoring)
6. **My Tagged Notes** (NEW — content authoring, paired with templates)
7. **My Preferred Vendors** (NEW — workflow personalization)
8. **My Internal Resources** (NEW — content library)
9. Branding (existing — visual, placeholder)
10. AI Configuration (existing — placeholder)
11. Task Templates (existing — link out to `/admin/task-templates`)
12. Help & Tour (existing)
13. Danger Zone (existing)

**Notifications section** — `<NotificationPrefsMatrix>` with categories × channels grid + a sub-card **"Closed-transaction reminders"** with toggles per rule and an "Add custom reminder" CTA.

**My Closing Checklist Templates section** — Two side-by-side editors: Buyer + Seller. Each has section fields: Closing Expectations / Utility Transfer Guide / Address Change Guide / (seller only) Escrow Overage Reminder. Read-only **"Team template"** caption appears below each if a team template exists for that section ("Your team's template is shown below; your edits override it for your transactions only"). **"Preview printed sheet"** button below the editors opens `PrintChecklistModal` in preview mode.

**My Tagged Notes section** — `<TaggedNotesEditor>` — repeating rows of `{ tag chips (buyer|seller|both|fsbo|cash|financed|investor|owner_occupied|all), title, body }`.

**My Preferred Vendors section** — `<PreferredVendorsPicker>` — typeahead over `/api/v1/vendors`, multi-select, drag-handle reorder. Below the picker: read-only **"Team list"** card showing inherited team vendors.

**My Internal Resources section** — `<InternalResourcesPanel>` — grouped by category (Utility Companies, County Resources, Address Change Guide, Closing Guide, Other). Upload via dropzone. Below user resources: read-only **"Team resources"** list showing team-owned resources.

**Acceptance click path (Agent):**
1. Agent → topbar avatar → Settings.
2. Sticky nav → click **My Closing Checklist Templates** → buyer template editor focused.
3. Type three buyer closing expectations → Save → toast.
4. Click **Preview printed sheet** → modal opens with both sheets using your templates.
5. Sticky nav → **My Tagged Notes** → add note tagged `seller` "Remind about escrow overage" → Save.
6. **My Preferred Vendors** → typeahead select 2 vendors → drag reorder → Save.
7. **My Internal Resources** → drop "Denver County utility companies.pdf" → category Utility Companies → row appears.
8. **Notifications** → flip "Daily summary → email" off → toast.

### 6.D Client Portal — Profile Modal + Settings page

**Profile:** Client uses the shared `ProfileModal` (§6.B) — no separate `/client/profile` route.

**`/client/settings`** (NEW page): three cards — Notifications, Milestone Sharing Defaults, Agent BIO (read-only).

**Avatar menu routing rule:** Client clicks avatar → "Profile" → opens `ProfileModal`; clicks "Settings" → navigates to `/client/settings`. Two explicit menu items, NOT one "Profile" item that conflates both. The Profile entry does NOT navigate — it overlays the current page.

**Acceptance click path:**
1. Client → avatar → **Profile** → modal opens (no nav); edit phone → Save → toast; modal closes; still on previous page.
2. Avatar → **Settings** → navigates to `/client/settings`; 3 cards visible.
3. Change default link expiry → Save; create new share link → expiry preselected.
4. Agent BIO card shows the agent's bio (from agent's `profile_settings_json['agent_bio']`).
5. "Learn more about your agent →" link → `/client/agent` (existing M5.1, lightly extended).

### 6.E FSBO Portal — Profile Modal + Settings page

**Profile:** FSBO uses the shared `ProfileModal` (§6.B) — no separate `/fsbo/profile` route.

**`/fsbo/settings`** (NEW page): four cards — Notifications, Milestone Sharing Defaults, Support / Guide Contact Preferences, FSBO Boundary Notice (informational, fixed). "Open share management" CTA opens the existing `FsboShareManagementModal`.

**Avatar menu:** identical pattern to Client — separate "Profile" (modal) and "Settings" (navigates) entries.

**Acceptance click path:** mirrors §6.D with the additional Support card.

### 6.F Admin Team-Configuration Pages (FOUR NEW PAGES)

Each is a single-card admin surface using `AdminPageHeader` per `STYLE_GUIDE.md §15.2`:

**`/admin/team-checklist-templates`** — Two-column editor (Buyer + Seller) reusing the same `BuyerChecklistTemplateEditor` and `SellerChecklistTemplateEditor` components that ship under Settings. A team selector at the top (Admin only — TL sees their team locked). Save → toast; audit log row `team_checklist_templates_update`.

**`/admin/team-tagged-notes`** — Reuses `TaggedNotesEditor`. Same team selector.

**`/admin/team-vendors`** — Reuses `PreferredVendorsPicker`.

**`/admin/team-internal-resources`** — Reuses `InternalResourcesPanel` with `team_owned=true` write target.

**Sidebar placement:** All four under the existing **Admin** menu group (alongside Users, Task Templates, Audit Logs, AI Governance, Tenant Settings, Payment Access, Vendor Templates, Communications). NOT under the "Team" sidebar group.

**Acceptance click path (Team Lead):**
1. TL → sidebar **Admin → Team Checklist Templates** → opens with own team selected.
2. Edit Team Buyer Template Closing Expectations → Save → toast; audit log records `team_checklist_templates_update`.
3. Sign in as an Agent on the same team → Settings → My Closing Checklist Templates → read-only caption "Your team's template is shown below" displays the TL's edits.
4. Agent overrides one section → Save → only their override displays for their own transactions; team value still inherited by other members.
5. Same flow for the other three admin pages.

### 6.G AI Closing Checklist Generator — `PrintChecklistModal`

(unchanged from v1.0 § 6.E — just renumbered)

Component: `src/components/profile/print/PrintChecklistModal.tsx`. Triggered from Solo Agent / Team Leader dashboards, Active Transactions card footer, Transaction Detail, and Settings → My Checklist Templates "Preview".

Modal layout, fetch contract, and acceptance click path are the same as v1.0 — the **template_source** caption now reads "Source: your personal template / your team's template / system default" reflecting the inheritance chain.

### 6.H Natural-Language Task Creation — `AiNlpTaskModal`

(unchanged from v1.0 § 6.F)

Two-step modal triggered from "✦ Quick add" on Active Tx drawer and Task Queue. NL textarea → review parsed payload with per-field confidence chips → save via existing `POST /api/v1/tasks`.

### 6.I Dynamic Task Intelligence — `/ai-suggestions` rebuild + per-deal strip

(unchanged from v1.0 § 6.G)

Page rebuild per `completed_designs/ve-intelligence-ai_suggestions.html`. Per-deal strip in expanded drawer (top 3). Bulk Accept preview modal for TL.

### 6.J Post-Closing Feedback — `PostClosingFeedbackModal`

(unchanged from v1.0 § 6.H)

Auto-fires on first view within 7 d of close. Manual re-open from Closed transactions list and Transaction History panel.

### 6.K Sidebar + avatar-menu updates

- Add **Brokerage Overview** + 4 team-config pages inside the existing **Admin** sidebar group (TL/Admin gated). NOT under Team.
- Wire the existing AI Suggestions sidebar link (Intelligence group) to the rebuilt page.
- **Avatar menu — every role** gets three explicit entries:
  1. **Profile** → calls `useProfileModal().open()`. Does NOT navigate.
  2. **Settings** → navigates to the role's Settings route (`/settings`, `/client/settings`, `/fsbo/settings`).
  3. **Sign out** → existing.
- The current implementation only shows "Settings" + "Sign out" — M5.3 adds the Profile entry.
- The sidebar profile chip at the bottom of the dark sidebar (internal roles) keeps its current behavior: click → opens the avatar menu inline. Same three entries.

### 6.L Components inventory (NEW)

| Component | Used in |
| --- | --- |
| `pages/admin/AdminBrokerageOverviewPage.tsx` | `/admin/brokerage` |
| `pages/admin/AdminTeamChecklistTemplatesPage.tsx` | `/admin/team-checklist-templates` |
| `pages/admin/AdminTeamTaggedNotesPage.tsx` | `/admin/team-tagged-notes` |
| `pages/admin/AdminTeamVendorsPage.tsx` | `/admin/team-vendors` |
| `pages/admin/AdminTeamInternalResourcesPage.tsx` | `/admin/team-internal-resources` |
| `pages/client/ClientSettingsPage.tsx` | `/client/settings` |
| `pages/fsbo/FsboSettingsPage.tsx` | `/fsbo/settings` |
| `components/profile/ProfileModal.tsx` | Avatar menu → Profile (all roles) |
| `contexts/ProfileModalContext.tsx` | Provides `useProfileModal()` hook; single mount at app root |
| `components/profile/print/PrintChecklistModal.tsx` | Print Checklist buttons + Settings preview |
| `components/profile/templates/BuyerChecklistTemplateEditor.tsx` | Settings + Admin Team Templates |
| `components/profile/templates/SellerChecklistTemplateEditor.tsx` | Settings + Admin Team Templates |
| `components/profile/templates/TaggedNotesEditor.tsx` | Settings + Admin Team Tagged Notes |
| `components/profile/templates/PreferredVendorsPicker.tsx` | Settings + Admin Team Vendors |
| `components/profile/resources/InternalResourcesPanel.tsx` | Settings + Admin Team Internal Resources |
| `components/profile/notifications/NotificationPrefsMatrix.tsx` | Settings + Client Settings + FSBO Settings |
| `components/profile/notifications/ClosedTxReminderEditor.tsx` | Inside Settings Notifications sub-card |
| `components/tasks/AiNlpTaskModal.tsx` | "✦ Quick add" on Active Tx drawer + Task Queue |
| `components/ai-suggestions/AiSuggestionCard.tsx` | `/ai-suggestions` + per-deal strip |
| `components/ai-suggestions/AiSuggestionStrip.tsx` | Active Tx drawer (top 3) |
| `components/ai-suggestions/BulkAcceptPreviewModal.tsx` | `/ai-suggestions` (TL only) |
| `components/active-transactions/PostClosingFeedbackModal.tsx` | Auto-fires + manual re-open |
| `hooks/useProfileModal.ts` | Returns `{ open, close, isOpen }` from `ProfileModalContext` |
| `hooks/useProfileSettings.ts` | Reads/writes the whitelisted `profile_settings_json` keys |
| `hooks/useUserChecklistTemplates.ts` | Reads/writes user templates + reads team templates |
| `hooks/useUserPreferredVendors.ts` | Reads user list + team list (hydrated) |
| `hooks/useUserInternalResources.ts` | Reads user list + team list |
| `hooks/useTeamChecklistTemplates.ts` (admin) | TL/Admin team-template editor |
| `hooks/useAiSuggestions.ts` | List / accept / dismiss with optimistic UI |
| `hooks/useNotificationPrefs.ts` | Reads/writes notification matrix |
| `hooks/useClosingChecklist.ts` | Fetches two-sheet response |

---

## 7. Workstream Tickets — Sequenced Backlog

Total: 7 working days within the calendar week (Mon–Sun 2026-07-13 → 2026-07-19). Day 7 is buffer + manual QA + tester walk-through.

### Slice 0 — Guardrails & alignment (Day 0, pre-week)

- [ ] Confirm M5.2 has landed; M5.3 migration timestamps must be strictly greater.
- [ ] Re-read `MILESTONE_5_2_UX_IMPROVEMENT_PLAN.md` — apply the same deal-anchored mental model to every M5.3 surface.
- [ ] Verify the AI provider abstraction is healthy on dev.
- [ ] Inventory check: confirm `components/profile/{print,resources,templates}/` and `pages/profile/` are still empty. `components/profile/notifications/` does not exist yet — M5.3 creates it.
- [ ] **Schedule the real-estate-professional tester walk-through for Day 6 end-of-day.**

### Slice 1 — Foundation: schema + profile data layer (Days 1–2)

- [ ] Migration `20260802090000_milestone_5_3_personalization.sql` (§5.J).
- [ ] `UserRepository.update_profile_settings` deep-merge + whitelist + tests.
- [ ] `notification_prefs_service.py` (§3.1) + tests verifying existing notification paths route through `should_notify(...)`.
- [ ] Extend `PATCH /api/v1/users/me` to accept the whitelisted `profile_settings` body.
- [ ] Add `closing_checklist.build_two_sheet_checklist` (§5.F) with unit tests for all sections + the 3-level fallback chain.
- [ ] Add the five Settings endpoint groups (§5.C) — handlers + tests.
- [ ] Add the four Admin team-config endpoint groups (§5.D) — handlers + tests.
- [ ] **Tests:** `test_profile_settings_whitelist.py`, `test_notification_prefs_service.py`, `test_closing_checklist_two_sheet.py`, `test_my_settings_endpoints.py`, `test_admin_team_endpoints.py`.

### Slice 2 — Settings UI extension + ProfileModal + Reports migration (Days 2–4)

- [ ] Extend `pages/settings/SettingsPage.tsx` with five new sections in the documented sort order (§6.C). Sticky nav grows to 13 items.
- [ ] Build `NotificationPrefsMatrix` + `ClosedTxReminderEditor`.
- [ ] Build `BuyerChecklistTemplateEditor`, `SellerChecklistTemplateEditor`, `TaggedNotesEditor` — designed for reuse by Admin team pages.
- [ ] Build `PreferredVendorsPicker` (typeahead + reorder).
- [ ] Build `InternalResourcesPanel` (upload + list + delete).
- [ ] Build `ProfileModal` + `ProfileModalContext` (§6.B). Mount the provider at app root.
- [ ] Add avatar-menu "Profile" entry for every role; wire to `useProfileModal().open()`.
- [ ] Wire deep-merge save semantics per Settings section.
- [ ] **Reports tab migration:** Move the M5.1 `/profile?tab=reports` content to `/analytics?scope=me` with a "My reports" sub-nav tab. Delete `UserProfilePage.tsx`. Add 301 redirect `/profile → /analytics?scope=me` in `App.tsx`. Delete the empty `pages/profile/` directory.
- [ ] Update `FRONTEND_UI_WORKFLOW_LOGIC.md §11.1` from "Profile — page" to "Profile — modal" (one-line spec amendment).
- [ ] **Tests:** RTL tests for each new Settings section + `ProfileModal.test.tsx`.

### Slice 3 — Admin team pages + Brokerage Overview + Client/FSBO Settings (Days 3–5)

- [ ] Build `/admin/brokerage` (`AdminBrokerageOverviewPage`).
- [ ] Build the four `/admin/team-*` pages reusing Settings component primitives.
- [ ] Add sidebar Admin group items (gated TL/Admin).
- [ ] Build `/client/settings` and `/fsbo/settings` pages (no `/client/profile` or `/fsbo/profile` — those are the shared ProfileModal).
- [ ] Verify Client/FSBO avatar menus show Profile (opens modal) + Settings (navigates) entries.
- [ ] Backend stubs for `/api/v1/admin/brokerage/overview` and the four `/api/v1/admin/team-*` endpoints.

### Slice 4 — Closing Checklist Modal (Day 5)

- [ ] Build `PrintChecklistModal` with @media-print CSS and both-sheets preview.
- [ ] Swap existing Print Checklist buttons to open the modal.
- [ ] Add **Preview printed sheet** in Settings → My Checklist Templates.
- [ ] **Tests:** `PrintChecklistModal.test.tsx`.

### Slice 5 — NLP + AI Suggestions inbox + per-deal strip (Days 5–6)

- [ ] `POST /api/v1/tasks/parse-nl` + `ai_service.parse_natural_language_task`.
- [ ] Build `AiNlpTaskModal` (two-step, confidence chips).
- [ ] Add ✦ Quick add buttons.
- [ ] `ai_suggestions` table + CRUD endpoints.
- [ ] Rebuild `AISuggestionsPage` + `AiSuggestionCard`.
- [ ] Build `AiSuggestionStrip` for the per-deal drawer.
- [ ] Build `BulkAcceptPreviewModal` (TL only).
- [ ] Hook existing `/ai/recommend-tasks` to persist into `ai_suggestions` with dedup.
- [ ] Wire **Recommend tasks for this deal** explicit CTA on the Active Tx drawer.
- [ ] **Tests:** `test_nl_task_parsing.py`, `test_ai_suggestions_api.py`, `test_ai_suggestion_dedup.py`, RTL tests.

### Slice 6 — Post-closing feedback + closed-tx reminders + audit + tester walk-through (Days 6–7)

- [ ] Build `PostClosingFeedbackModal` (auto-fire on first view within 7d of close).
- [ ] `POST /api/v1/ai/suggestion-feedback` + DB + capped corpus + prompt context wiring.
- [ ] `closed_transaction_reminder_service.py` + manual-trigger admin endpoint for QA.
- [ ] Wire `closed_transaction_reminder` category into the matrix.
- [ ] Audit logging verification (every M5.3 write writes a row).
- [ ] Run all acceptance click paths in §6.
- [ ] **Real-estate-professional tester walk-through.** Record friction; blocking issues fixed on Day 7.
- [ ] `/security-review` skill on the diff.
- [ ] Accessibility audit (`axe-core`).
- [ ] Print rendering verified Chrome/Safari/Firefox/Edge A4 + Letter.
- [ ] White-label theming verified on every new surface.

---

## 8. Visual Consistency Rules

Unchanged from v1.0 §8 — every M5.3 surface uses one card vocabulary, mono kickers, `ve-*` tokens only, paired status pills, `tabular-nums lining-nums`, the canonical 380px discard dialog, never `window.confirm()` / native `<select>`, explanatory empty states, AI-only champagne accents, explicit action buttons (no whole-card click targets), `px-3 md:px-6` page gutter, no `max-w-*` on internal pages, grip-handle + keyboard reorder.

**Settings page-specific:** New sections follow the existing `SettingsPage` Section component shape — heading + description + body + Save action where applicable. No bespoke per-section chrome.

**Admin page-specific:** All five new admin pages use `AdminPageHeader` for the breadcrumb-style header per `STYLE_GUIDE.md §15.2`. Same as existing admin pages.

---

## 9. Money / Numeric Conventions

Unchanged from v1.0 §9.

---

## 10. Testing Strategy

### 10.1 Backend unit + integration

Target **+70–90 new tests**:

- `test_profile_settings_whitelist.py` — only whitelisted keys accepted; unknown keys 400.
- `test_user_profile_settings_deep_merge.py` — saving one key does not wipe another.
- `test_notification_prefs_service.py` — `should_notify` returns the right value for every category × channel; new categories default-on preserve back-compat.
- `test_closing_checklist_two_sheet.py` — all 7 Agent-sheet and 6 Client-sheet sections render; 3-level fallback (user → team → tenant_default) works; no profile templates set falls back gracefully.
- `test_admin_brokerage_overview.py` — KPI numbers reconcile; non-permitted role 404.
- `test_admin_team_*.py` (×4) — TL can only edit own team; Admin can edit any team in tenant; cross-tenant 404; audit logs written.
- `test_my_settings_endpoints.py` (×5 sections) — read/write/inheritance preview works.
- `test_nl_task_parsing.py` — sample patterns; deterministic confidence per input; prompt-injection attempts rejected.
- `test_ai_suggestions_api.py` — list / accept / dismiss; dedup index; status transitions; `scope='all_future'` from non-TL returns 409.
- `test_post_closing_feedback.py` — one submission per user per tx (idempotent); corpus update; prompt-context wiring.
- `test_closed_tx_reminders.py` — daily cron fires per cadence; respects `should_notify`.
- `test_internal_resources.py` — upload writes; list filters; team-owned vs user-owned scoping; cross-user 403.
- `test_user_preferred_vendors.py` — saves ordered list; FK enforces vendor existence; team fallback when user list empty.
- `test_audit_m5_3.py` — every M5.3 write writes an audit row with before/after diff.

### 10.2 Frontend

RTL render tests for every new page + modal:

- `ProfileModal.test.tsx` — opens via `useProfileModal().open()`; renders all identity fields; hides `company_name` for Client/FSBO/Vendor roles; Save sends `PATCH /api/v1/users/me` with the partial; unsaved-changes guard on close.
- `SettingsPage.test.tsx` — 13 sticky nav items render in the documented order; each new section renders with empty state when no data; save mutations send the correctly-scoped partial.
- `AnalyticsPage.test.tsx` — verifies the new `?scope=me` query param + "My reports" sub-nav tab (Reports migration target).
- `App.test.tsx` (route table) — `/profile?tab=reports` 301-redirects to `/analytics?scope=me`; `/profile` (no params) redirects to `/analytics?scope=me`.
- `AdminBrokerageOverviewPage.test.tsx` — KPIs render; row clicks deep-link correctly; non-permitted role 404.
- `AdminTeam*Page.test.tsx` (×4) — TL editor saves; Admin editor with team selector saves; cross-team Admin role works.
- `ClientSettingsPage.test.tsx` + `FsboSettingsPage.test.tsx` — render + save flows. Avatar menu shows Profile + Settings + Sign out entries; Profile opens modal (no nav); Settings navigates.
- `PrintChecklistModal.test.tsx` — both sheets render; tab switch; print filter.
- `AiNlpTaskModal.test.tsx` — two-step flow; confidence chips; Save posts the user-confirmed payload.
- `AISuggestionsPage.test.tsx` — list / filter / slider / Accept / Dismiss.
- `BulkAcceptPreviewModal.test.tsx` — TL-only visible; preview tally accurate.
- `PostClosingFeedbackModal.test.tsx` — auto-fires in window; idempotent post-submission.

`tsc --noEmit` + `eslint --max-warnings 0`. Zero console errors on every new route.

### 10.3 Manual QA — end-to-end via dev environment

Run on dev with a real-estate-professional tester (scheduled in Slice 0):

**Tester click-paths** (each ends with a screenshot saved to the QA log):

| # | Path | Pass criterion |
| --- | --- | --- |
| 1 | Agent on any page → avatar menu → Profile → modal opens overlaying current page → edit bio + company + avatar → Save → modal closes; user still on original page → log out, back in → avatar → Profile → values persisted | Identity persists; Profile is modal (no navigation) |
| 1a | Agent → `/profile?tab=reports` in address bar → 301-redirects to `/analytics?scope=me` with "My reports" sub-nav tab focused | Reports migration works; no broken bookmarks |
| 2 | Agent → avatar → Settings → fill all five new sections (Notifications, Checklist Templates, Tagged Notes, Preferred Vendors, Internal Resources) → log out, back in → all persisted | Settings persist; no section wiped another |
| 3 | Settings → My Checklist Templates → Preview printed sheet → save PDF → template content visible | Template renders verbatim |
| 4 | Active Tx card → Print Checklist → switch to Client Sheet → Print → save PDF → no internal info | Client sheet customer-safe |
| 5 | Settings → Notifications → flip "Daily summary → email" off → trigger daily summary → no email | Toggle honored |
| 6 | Active Tx drawer → ✦ Quick add → "Send buyer inspection contingency reminder three days before inspection" → Parse → confirm → Save → task appears | NL → structured → saved |
| 7 | TL → /ai-suggestions → Accept all above 90% → preview → Apply → tasks added across deals | Bulk apply with preview |
| 8 | Mark a tx Complete → re-open it → feedback modal auto-fires → submit → no re-fire on subsequent views | Feedback once |
| 9 | Admin → /admin/brokerage → KPIs visible; click agent row → /admin/users/:id | Navigation works |
| 10 | TL → /admin/team-checklist-templates → edit team buyer template → log in as different team member → Settings → My Checklist Templates → see "Your team's template" caption with TL's edits | Team inheritance works |
| 11 | Client → avatar → Profile → modal opens (no navigation) → edit phone → Save; then avatar → Settings → flip a notification → both persisted | Client modal + Settings split works |
| 12 | FSBO → /fsbo/settings → set support contact preference → confirmed in subsequent outbound | FSBO preferences honored |
| 13 | Agent → typing `/admin/brokerage` in URL → 404 | Route gating works |
| 14 | Tenant admin changes brand color → reload Profile, Settings, Admin pages, Print sheet → new color applied | White-label propagation |

**Tester walk-through script** (plain English, no jargon):

> 1. Log in as the agent we set up for you.
> 2. Click your name (top right) → click "Profile". A small window should appear over the page (a "modal"). It should contain your name, email, phone, company, bio, and avatar. Edit your bio, add your company. Click Save. The window closes; you should still be on the same page you started on. Click your name → Profile again to confirm your changes saved.
> 3. Click your name → click "Settings". This time a full page should load (NOT a small window). A long page with a left navigation bar appears. Scroll the nav. You should see 13 items including new ones: Notifications, My Closing Checklist Templates, My Tagged Notes, My Preferred Vendors, My Internal Resources.
> 4. Click "My Closing Checklist Templates". Type three things you tell first-time buyers at closing. Save. Click "Preview printed sheet". Confirm the print preview shows your text.
> 5. Click "My Preferred Vendors". Type a vendor name. Pick two. Drag one to first. Save.
> 6. Click "My Internal Resources". Drag a PDF into the box. Pick "Utility Companies" category. Confirm upload.
> 7. Click "Notifications". Flip one toggle off.
> 8. Go to "Active Transactions". Pick any deal. Click to expand. In Tasks, click "✦ Quick add". Type one sentence describing a task. Click Parse. Verify and Save.
> 9. Click sidebar "AI Suggestions". Verify at least one card. Accept one.
> 10. Click a closed transaction. A feedback modal should appear. Mark a few tasks. Submit.
> 11. Tell us what was confusing.

### 10.4 Security

- `/security-review` on diff.
- OWASP focused review: IDOR on internal resources, mass-assignment on PATCH endpoints with whitelist enforcement, JSON injection / HTML sanitization in template editors, storage path traversal on upload, LLM prompt injection on NLP parser.
- Confirm no PII leaks in audit summaries.

### 10.5 Accessibility

`axe-core` clean; keyboard-only walk-through; VoiceOver/NVDA smoke test on the new Settings sections, Admin team pages, and AI Suggestions inbox.

---

## 11. Risk Register

Twenty items carried over from v1.0 + three added for the v2.0 realignment (#21–23) + three added for the v2.1 Profile-as-Modal refinement (#24–26). Total: 26.

| # | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| 1 | Settings section save wipes another section's JSONB | Med | High | Deep-merge helper + whitelist + dedicated tests. Code-review gate: every M5.3 PATCH endpoint goes through the helper. |
| 2 | NLP task parser hallucinates a due date | Med | Med | Per-field confidence chip; human confirm before save. |
| 3 | AI Suggestions inbox floods with duplicates | High | Med | `dedup_hash` unique index; 30-day expires_at. |
| 4 | TL bulk Accept applies a suggestion across deals it shouldn't | Med | High | Bulk Accept always opens preview modal. |
| 5 | Post-closing modal nags users who already submitted | Low | Med | `ai_suggestion_feedback` unique on `(tx, user)`; localStorage 7d cooldown on Skip. |
| 6 | Background generator for AI suggestions is out of scope; inbox starts empty | High | Low | Explicit "Recommend tasks for this deal" button in Slice 5 makes inbox testable. Background trigger documented as post-MVP follow-up. |
| 7 | Closed-tx reminder cron has no scheduler infrastructure | Med | Med | Hook into M4.1 retention purge cron; ship manual-trigger admin endpoint as fallback for QA. |
| 8 | Printed checklist doesn't render correctly across browsers | Low | High | QA matrix Chrome/Safari/Firefox/Edge A4 + Letter. |
| 9 | Internal Resources storage grows unbounded | Low | Low | Per-file 20 MB cap; tenant-level quota documented as future enhancement. |
| 10 | Profile preview sheet uses dummy data that doesn't match real composition | Med | Low | Dummy data sourced from the same composition code path. |
| 11 | Tester walk-through reveals workflow break with 2 days left | Med | High | Day 7 buffer reserved for fixes. |
| 12 | "✦ Quick add" visually competes with "+ Add Task" | Med | Low | Style as secondary outline with `✦` glyph in `ve-orange`; primary stays "+ Add Task". |
| 13 | Mass-assignment on `PATCH /users/me { profile_settings }` lets a client overwrite something they shouldn't | Med | High | Server-side whitelist; reject unknown keys with 400. |
| 14 | LLM prompt injection on NL task parsing | Med | Med | System prompt + JSON-schema output validation. |
| 15 | Feedback corpus in `tenants.settings_json` grows unbounded | Med | Low | Capped at 500 FIFO. |
| 16 | Profile/Settings/Admin density confuses non-technical testers | Med | High | Each Settings section opens with one card + one CTA; tester walk-through plain-English script. |
| 17 | Auto-fired post-closing modal interrupts work | Med | Med | Esc / Skip dismiss; localStorage 7d cooldown. |
| 18 | "Team inheritance" caption on Settings is unclear when team value is empty | Med | Low | Caption hidden when no team value exists; appears the moment TL saves one. |
| 19 | Audit log volume balloons | Med | Low | Diff bounded to actual JSONB change; 2y retention from §10.3. |
| 20 | Brokerage page becomes stale snapshot | Low | Low | "Last refreshed" timestamp + manual refresh button. |
| **21 (NEW)** | **Settings page becomes too long to scan** (13 sections) | **Med** | **Med** | **Sticky left-rail nav with section anchors stays visible on screens ≥1024px; scroll-spy highlights the active section (the existing pattern handles this). Tester walk-through specifically asks "could you find each section?" — friction here triggers a re-grouping decision on Day 7.** |
| **22 (NEW)** | **TL confused about which section belongs on Settings vs. Admin** | **Med** | **High** | **Settings → Checklist Templates / Tagged Notes / Vendors / Internal Resources sections each display a small inline link: "Manage team-wide values in Admin →" (Admin/TL only) — making the relationship explicit. Acceptance criterion #10 specifically validates the team-inheritance flow end-to-end.** |
| **23 (NEW)** | **Avatar menu still shows only "Settings" without explicit Profile entry** | **Low** | **Low** | **Add explicit "Profile" + "Settings" entries to the avatar dropdown for every role (verify Client/FSBO too). Verify in tester walk-through step 2.** |
| **24 (v2.1)** | **`FRONTEND_UI_WORKFLOW_LOGIC.md §11.1` documents Profile as a page; v2.1 ships it as a modal** | **Low** | **Med** | **Spec amendment in Slice 2: change "Profile — `/profile`" to "Profile — `ProfileModal` (no route)" in §11.1. Cross-reference Workflow L (§13 in the workflow doc) which describes "Profile & Settings Flow" — update step 1 from "Personal info" to "Personal info (modal)". Low-risk because no Phase 3+ implementation has been built against the old spec yet for this surface (the existing `/profile` is the slim two-tab page from M5.1; that's what we're replacing).** |
| **25 (v2.1)** | **Reports tab migration to `/analytics` reveals charts are not actually per-user-filterable** | **Low** | **Med** | **The M5.1 `/analytics` page already supports `?agent_id=` per the existing code. Slice 2 includes a 30-min verification: open `/analytics?agent_id={me}` for a non-admin agent and confirm the charts re-scope. If they don't, the migration ticket grows; defer if the lift exceeds half a day and ship the modal anyway — the deleted `UserProfilePage` Reports tab content goes into a new `/me/reports` route as a fallback (1 hour to ship, looks identical to the deleted tab).** |
| **26 (v2.1)** | **ProfileModal opens over a page whose own modal is also open** (z-index collision) | **Low** | **Med** | **Per `STYLE_GUIDE.md §6.5`, modal-over-modal pattern uses radix primitives directly with `z-[650]` overlay and `z-[660]` content. ProfileModal uses the standard `z-50` mount because it should never co-exist with another modal — the avatar menu auto-closes any open transient overlay before opening. Verified in RTL test: open AddTaskModal → open avatar menu → click Profile → AddTaskModal silently closes (no nested-modal state).** |

---

## 12. Acceptance Criteria — mapped to `milestones.txt` §5.3

Every line below is testable end-to-end via the UI by a non-developer real-estate professional. No backend-only or "logs verify" criteria.

| Deliverable | Verification (click-path; no code reading required) |
| --- | --- |
| **Brokerage profile (all agents/teams in one dashboard)** | Admin/TL → sidebar Admin → Brokerage Overview → KPI strip with Agents / Teams / Active Tx / Pipeline; tables of agents + teams; row drill-down works; non-permitted role 404s. |
| **Agent/team profile — identity (modal)** | Any role on any page → topbar avatar → Profile → modal opens overlaying current page (no navigation) → edit name/phone/bio/company/avatar → Save → modal closes, user remains on original page. Client/FSBO/Vendor see modal without Company field. |
| **Reports migration** | Visiting `/profile?tab=reports` 301-redirects to `/analytics?scope=me` → "My reports" sub-nav tab is pre-selected → same per-user charts that the deleted tab displayed are now visible there. |
| **Agent/team profile — Internal document center (personal)** | Settings → My Internal Resources → drag-drop PDF → assigns category → persists across refresh; downloadable; deletable. |
| **Agent/team profile — Internal document center (team-wide)** | TL/Admin → Admin → Team Internal Resources → upload PDF; same file visible to all team members in their Settings → My Internal Resources as a "Team resource"; non-team-member doesn't see it. |
| **Agent/team profile — Preferred vendors (personal)** | Settings → My Preferred Vendors → typeahead select → drag reorder → Save → persists. |
| **Agent/team profile — Preferred vendors (team-wide)** | TL/Admin → Admin → Team Vendors → set list → Agent on team sees the team list as inherited in their Settings; their own list overrides. |
| **Agent/team profile — Buyer and Seller closing checklist templates (personal)** | Settings → My Closing Checklist Templates → edit both → Preview printed sheet → opens with edited content. |
| **Agent/team profile — Buyer and Seller closing checklist templates (team-wide)** | TL/Admin → Admin → Team Checklist Templates → edit → Agent on team sees the team templates in their Settings → My Checklist Templates as inherited; their override applies only to their own transactions. |
| **Agent/team profile — Tagged note management for checklist printing (personal)** | Settings → My Tagged Notes → add note tagged `seller` → on a Seller transaction, Print Checklist → note appears in Tagged Notes section. |
| **Agent/team profile — Tagged note management for checklist printing (team-wide)** | TL/Admin → Admin → Team Tagged Notes → add note → appears for all team members on matching transactions. |
| **Agent/team profile — Seller escrow-overage reminder defaults** | Settings → My Checklist Templates → set escrow overage reminder text in seller template → Print Seller transaction's checklist → reminder appears. |
| **Agent/team profile — Closed transaction reminders (tax exemptions, reviews)** | Settings → Notifications → Closed-tx Reminders sub-card → add rule "Tax exemption 60d" → admin runs cron manually for a tx closed 60 days ago → email + in-app notification arrive. |
| **Agent/team profile — Notification preferences (on/off)** | Settings → Notifications → flip any category × channel toggle → notification path no longer fires (or starts firing); persists across refresh. |
| **Client portal — Milestone sharing** | Client → /client/settings → set default link expiry to 7d → create new share link → 7d preselected; viewer-open alerts honored per toggle. |
| **Client portal — Agent BIO / Learn About Your Agent** | Client → /client/settings → Agent BIO card visible with agent's photo, name, company, bio (sourced from agent's `profile_settings_json['agent_bio']`), phone, email. "Learn more →" link → /client/agent (extended). |
| **Client portal — Notification preferences** | Client → /client/settings → flip a client-relevant category → behavior changes. |
| **FSBO portal — Notification preferences management** | FSBO → /fsbo/settings → flip a category → behavior changes. |
| **FSBO portal — Milestone sharing preferences** | FSBO → /fsbo/settings → change defaults → new share-link UI honors them. |
| **FSBO portal — Support/guide contact preferences** | FSBO → /fsbo/settings → "Phone preferred 9am–5pm" → next outbound from Velvet Elves support records the preference. |
| **AI closing checklist generator — Agent sheet + Client sheet** | Active Tx card → Print Checklist → modal with both tabs → each tab prints the correct sheet. |
| **AI closing checklist generator — Standard data per agent/team** | Agent A sees own templates; Agent B same team sees team template by default unless overridden; template_source caption visible. |
| **AI closing checklist generator — Dates, utility info, address change guides** | Printed Agent Sheet includes Utility Companies + key dates + escrow reminder. Printed Client Sheet includes utility transfer guide + USPS address-change guide + who-to-call. |
| **AI closing checklist generator — Print sourced from profile templates** | Editing Settings → My Checklist Templates buyer template, re-printing, results in updated content with no code change. |
| **Natural-language task creation** | Active Tx drawer → ✦ Quick add → type one sentence → Parse → review → Save → task in deal's list; raw text + parsed payload in audit log. |
| **Dynamic task intelligence UI — Recommendations with reasons/sources** | /ai-suggestions → each card shows confidence ring, type icon, title, description, source, reason, transaction link. |
| **Dynamic task intelligence UI — Approve/restore controls** | Accept on a card → applied; Dismiss → removed from default view but reachable via `?status=dismissed`; both audit-logged. |
| **Dynamic task intelligence UI — Bulk approval for team leads with preview** | TL → /ai-suggestions → Accept all above 90% → preview → Apply → audit log records per-tx applications. |
| **Task feedback loop UI (post-closing: useful/unnecessary/missing)** | Recently closed tx → modal auto-fires → submit → row in `ai_suggestion_feedback`; next `/recommend-tasks` for tenant uses "unnecessary" verdicts in system prompt. |

---

## 13. Out-of-Band Notes & References

- **AI Coach** is not part of M5.3. Future paid add-on. Architecture hooks preserved via `notification_prefs_service`.
- **ProfileModal + Settings + Admin pages are tenant-themable starting M6.1.** M5.3 uses `ve-*` tokens that already resolve to tenant theme variables; nothing breaks at M6.1.
- **`pages/profile/` empty directory deleted** as cleanup. **`pages/users/UserProfilePage.tsx` also deleted** — replaced by `ProfileModal` (identity) + `/analytics?scope=me` (Reports). 301 redirect `/profile → /analytics?scope=me` for back-compat.
- **The avatar menu pattern (Profile → modal; Settings → page) becomes the convention.** Future personal-action surfaces (Themes? Shortcuts? API tokens?) follow the rule: small + frequently-edited → modal; long + occasionally-edited → Settings section; team-wide → Admin page.
- **FRONTEND_UI_WORKFLOW_LOGIC.md §11.1 and Workflow L (§13) need a one-line amendment** in Slice 2. Treat this as a tracked deliverable, not "we'll get to the docs later" — workflow-spec drift is what triggered v2.0 (and arguably v1.0's flaws).
- **`recommend-tasks` becomes a persistent generator** — same input, response also persisted. Backwards-compatible.
- **Closed-tx reminder cron** mirrors M4.1 retention purge pattern.
- **AI provider abstraction unchanged** — M5.3 adds one new method (`parse_natural_language_task`); threads through same provider abstraction.
- **Avatar uploader** reuses existing Supabase Storage `user-avatars` bucket (M2.3).
- **Profile/Settings/Admin are the highest-traffic settings surfaces** — every internal user opens at least one weekly. Performance budget: under 500 ms TTI on dev with sections lazy-loaded.
- **Tester walk-through** is the single most important Slice 0 item.
- **Plan revision policy:** any deliverable shift updates §2.1 and §12 in the same commit.

---

## 14. Why This Plan Is Different — and How v2.0 + v2.1 Improve on v1.0

The prior milestone plans (M4.2, M4.3, M5.1, M5.2) all shipped functional backends and partial UI. The retros — captured in `MILESTONE_5_2_UX_IMPROVEMENT_PLAN.md` — show the same defect class repeatedly: backend ships, UI lags or is missing entry points; UI requires the user to know internal data the system already has; non-developer tester encounters dead-ends or features that exist but cannot be invoked from the UI.

v1.0 of this plan corrected those defects but introduced a *new* one: it conflated identity, preferences, and team-wide configuration onto a single 7-tab Profile page, producing functional overlap with the existing Settings page and silently relocating admin-scope work onto a per-user surface.

**v2.0 corrects v1.0 by establishing a strict three-surface separation (§0):**

1. **Profile = identity** — who I am.
2. **Settings = personal preferences** — how the system behaves for me. Extends the existing scrolling document with five new sections.
3. **Admin = team / tenant-wide configuration** — how the team is set up. Five new admin pages, one for each shared resource.

**v2.1 refines pillar 1: Profile is delivered as a shared `ProfileModal`, not a page.** Same surface category ("identity"), same backend, same field set — just a modal opened from the avatar menu instead of a route. The M5.1 Reports tab on `/profile` (a duplicate of `/analytics`) folds into `/analytics?scope=me` as part of the cleanup. The change removes three would-be routes, simplifies the avatar menu UX (Profile = quick edit without navigating; Settings = full page), and reinforces the rule that **Settings is the page; Profile is the quick edit**.

**v2.0 + v2.1 keep the original v1.0 strengths:**

- **Every deliverable has a click-path in §12** that a non-developer can execute end-to-end.
- **Every backend endpoint has a button** in the frontend.
- **Entry points are pluralized.** Print Checklist is reachable from 5 places. ✦ Quick add from 3. Settings sections from sidebar nav and direct anchor links. Brokerage from sidebar and Admin dashboard.
- **Tester walk-through is a Slice 0 dependency.** Day 7 buffer reserved for tester-feedback fixes.
- **Foundation audit (§3) is explicit** about what exists today.
- **Visual consistency rules are normative.**
- **Risk register is concrete and bounded** — 26 items (23 from v2.0 + 3 added for v2.1's modal/spec-deviation work), each with a specific mitigation.

**The single most important sentence in this plan, repeated for emphasis:**

> **Every deliverable in `milestones.txt` §5.3 has an acceptance criterion that a real-estate professional can execute through the UI in under five minutes without ever reading code or opening a terminal — AND the deliverable lives on the surface that matches the user's mental model (identity → Profile; preferences → Settings; team config → Admin).**

If a criterion in §12 cannot be met that way, the plan failed and must be revised before sign-off.

---

_End of plan (v2.1)._
