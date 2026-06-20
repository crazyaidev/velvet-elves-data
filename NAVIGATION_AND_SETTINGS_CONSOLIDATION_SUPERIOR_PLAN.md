# Navigation & Settings Consolidation - Superior Plan

**Status:** Plan only. No source changes. The five decisions are resolved (Section 11), and the plan has been corrected against the live source (Section 16 logs every fix). Awaiting Jake sign-off.
**Date:** 2026-06-19 (rev 2, after source verification)
**Author:** Jan (drafted with Claude)
**Scope:** The internal staff shell (`AppLayout`) - its left sidebar, its avatar menu, and every surface that is really a *setting* but is currently scattered across the sidebar, a modal, and a separate page. Portal shells (Client / FSBO / Vendor) are addressed explicitly but kept low-risk (Section 5.4). No backend authorization changes.
**Reference:** ListedKit settings page (two screenshots Jan supplied 2026-06-19) plus help.listedkit.com. The ListedKit model is one Settings hub, reached from the avatar menu, with cards grouped into "Personal Settings" and "Admin Settings", each card opening a focused detail page that breadcrumbs back to Settings.

---

## 0. Why I am writing this (and the standard I am holding it to)

Jan's instruction: the platform navigation is chaotic, and the worst part is that **settings and work are mixed together**. The goal is a standard, professional working environment where every setting lives in **one place**, and the sidebar is left holding only the work a real-estate professional actually does day to day.

Past plans were weak because they were drafted without a full reading of the product docs and the live source, so the end-to-end flow broke during testing. To avoid repeating that, this plan is built on a first-hand audit of:

- **Frontend source (the ground truth for what exists today):**
  - `src/App.tsx` - the full route table, role guards, and every redirect.
  - `src/components/ProtectedRoute.tsx` and `src/components/RoleRoute.tsx` - the two guard primitives, **including the workspace-owner bypass** (this materially affected the access matrix; see Section 16, fix F2).
  - `src/layouts/AppLayout.tsx` - `buildSection`, the sidebar groups, the avatar menu, the "Workspace owner" block.
  - `src/layouts/dashboardShellConfig.ts` - which sidebar groups each role sees.
  - `src/utils/constants.ts` - every route constant.
  - `src/components/account/AccountModal.tsx` + `sections/` - the personal-preferences modal.
  - `src/pages/settings/OpenAccountModalRoute.tsx` - the back-compat `/settings` handler.
  - `src/pages/organization/OrganizationPage.tsx` - the tenant/workspace config page (which today also hosts per-user Email + E-signature connection panes; see Section 16, fix F1).
  - `src/pages/admin/AdminTeamSettingsPage.tsx`, `src/pages/admin/*`, `src/pages/users/AdminUsersListPage.tsx`, `src/pages/EmailTemplatesPage.tsx`, `src/components/admin/AdminPageHeader.tsx`.
  - `src/hooks/useIntegrations.ts` and `velvet-elves-backend/app/api/v1/integrations.py` - confirmed that email and DocuSign integrations are **per-user**, not tenant-level (Section 16, fix F1).
- **Product docs:**
  - `FRONTEND_UI_WORKFLOW_LOGIC.md` - the as-built Shared Shell (the spec's intended sidebar groups are Dashboard / Deals / Workflow / Intelligence / Team, the avatar menu is meant to be "Settings, Profile, Sign Out", and onboarding tells users they can "connect Gmail / DocuSign later from Settings", which confirms email/e-sign are personal connections).
  - `STYLE_GUIDE.md` - the normative look and feel (Section 8 maps every rule I rely on).
  - `NAVIGATION_TEAM_ADMIN_REORG_PLAN.md` - the earlier Team-vs-Admin split (this plan supersedes and extends it; Section 13).
  - `SYSTEM_DESIGN.md` role model, the `COMPLETE_PLATFORM_PAYMENT_SYSTEM_CREDIT_WALLET_SUPERIOR_PLAN.md` (billing card), and the milestone plans that introduced each admin surface.

Holding principles, applied throughout:

- **One standard pattern, not a new invention.** Settings becomes a single hub that mirrors the ListedKit screenshot and every mainstream SaaS (Gmail, Stripe, Linear): avatar menu, then a card grid, then a focused detail page.
- **Mouse-first, minimal typing.** Every card is a large click target. The only typing anywhere is the optional "Search settings" box and the fields a user was always going to fill (their name, a template body).
- **Testable end to end by a non-developer.** Section 14 is a click-by-click script a real-estate tester can run per role with no dev knowledge.
- **Honest surfaces.** No demo data, no fabricated capabilities. Where a ListedKit card (active sessions, SMS) has no VE backend yet, I say so and leave it out rather than fake it.
- **No dead or 403 cards.** A card renders only if the signed-in user can actually reach and use its destination, derived from the real route guard (Section 5.3). This is the single rule that keeps the non-dev tester from ever hitting an "unauthorized" wall.
- **Brand-consistent and modern.** The hub uses the existing `ve-*` tokens, the serif/mono/sans three-voice hierarchy, and the canonical page shell.

---

## 1. The problem, stated precisely

"Settings" in Velvet Elves is currently spread across **five different entry mechanisms**, and several of them duplicate each other or mix personal and tenant concerns. A user who wants to change something has to guess which of the five holds it.

### 1.1 The five places settings live today

| # | Entry mechanism | How you reach it | What it holds |
| --- | --- | --- | --- |
| 1 | **Account modal** | Avatar menu - "Account" | Profile, Notifications, My Checklist Templates, My Tagged Notes, My Preferred Vendors, My Internal Resources, Help & tour |
| 2 | **Organization page** (`/organization`) | Avatar menu - "Organization" | Company, Branding, **Email connect (per-user)**, **E-signature (per-user)**, AI configuration, Billing & credits, Delete organization |
| 3 | **Sidebar "Team" group** | Left sidebar (TeamLead + Admin) | Team Overview, Teams, Team Members, Task Templates, Vendor Templates, Team Settings (playbook) |
| 4 | **Sidebar "Admin" group** | Left sidebar (Admin) | Communication Audit, AI Governance, Payment Access, Integrations, Advertising, Audit Log |
| 5 | **Sidebar "Workspace owner" block** | Left sidebar (non-Admin tenant owner) | Team, Members & invites, Workspace settings, Email & integrations |

Plus one **orphan**: `EmailTemplatesPage` (`/email-templates`) is a real settings surface (manage outbound email templates and signature) with **no sidebar entry at all**, reachable only from inside the Compose Email modal. Its route allows Agent / TC / TeamLead / Admin and **excludes Attorney** (verified in `App.tsx`).

### 1.2 The concrete failures this causes

1. **Settings are mixed into the work sidebar.** The "Team" and "Admin" groups sit in the same dark navy rail as Deals and Workflow, so configuration (Task Templates, Vendor Templates, Team Settings, AI Governance, Payment Access, Advertising, Integrations) reads as if it were daily work.
2. **The same destination appears under two labels.** "Workspace settings" (Owner block) and "Organization" (avatar menu) are the same page. "Members & invites" (Owner block) and "Team Members" (Team group) are the same `/admin/users`. "Email & integrations" (Owner block) overlaps with "Integrations" (Admin group) and with the Organization "Email" pane.
3. **The same feature is configured in two different surfaces.** AI is configured both on the Organization "AI configuration" pane (a stub whose three toggles are local component state, not persisted) and on the AI Governance page (the real provider + thresholds + automation surface). Style Guide 16.8 already says AI admin must live on one surface; today it lives on two.
4. **Personal and tenant concerns are bundled on one page.** The Organization page mixes tenant config (Company, Branding, Billing, Delete) with **per-user connections** (each user's own Gmail/Outlook inbox and DocuSign). Because the avatar "Organization" entry shows for every internal role, an Agent reaches their inbox connection through a page titled "Organization", next to brokerage branding they cannot edit.
5. **Personal vs team versions of the same editor are split across a modal and a page.** "My Checklist Templates / My Tagged Notes / My Preferred Vendors / My Internal Resources" live in the Account modal; their team equivalents live on the Team Settings page. Same editors, two homes, no signposting between them.
6. **A real settings surface has no home.** Email Templates is unreachable from navigation.
7. **The avatar menu disagrees with the spec.** The spec's Shared Shell says the avatar menu is "Settings, Profile, Sign Out"; the build shows "Account, Organization, Log Out". Neither matches a single Settings hub.

---

## 2. The categorization rule (so every surface has exactly one correct home)

> **A surface is WORK** if you use it to act on, or review the record of, live business objects (transactions, tasks, documents, calendar, payments, the vendor directory, clients, communications, the audit trail, team performance). Work surfaces stay in the **left sidebar**.
>
> **A surface is a SETTING** if you use it to configure how you, your workspace, or the AI behaves by default (your account, notification preferences, connected accounts, templates and playbooks, branding, billing, who has access, AI thresholds, payment permissions, advertising). Settings move into the **one Settings hub**.

Inside the hub there are two cuts, matching the ListedKit screenshot, but the cut is by **scope**, not by "is it admin":

> **Personal Settings** - configuration that affects only the signed-in user, including their own connected accounts. Every internal role sees these.
> **Workspace Settings** - configuration that affects the whole brokerage. Gated to Admin / Owner (a few are shared with Team Lead).

The scope cut is what fixes failure #4: a per-user connection (your inbox, your DocuSign) is **Personal** even though it is configuration, and it belongs with every internal user, not behind an Admin page.

Where a surface has a review side that is work and a configuration side that is a setting, the two are separated rather than duplicated. The clearest example is people: **Team Overview** (roster and performance you review) stays work in the sidebar, while **Users & Invites** (granting and revoking access) moves to Settings.

---

## 3. Page-by-page classification

| Surface (current location) | Verdict | Target home |
| --- | --- | --- |
| Active / Pending / Closed / All Transactions; Clients | Work | Sidebar - Deals |
| My Task Queue, All Documents, Closing Calendar | Work | Sidebar - Workflow |
| Invoices & Payments, Commission Payouts | Work | Sidebar - Payments |
| Vendor Directory | Work | Sidebar - Vendors |
| AI Suggestions, AI Email Review, Vendor Proposals, Analytics | Work | Sidebar - Intelligence |
| Team Overview (`/team`) | Work (review roster + performance) | Sidebar - Team |
| Communication Audit (`/admin/communications`) | Work (review the comms record) | Sidebar - Oversight |
| Audit Log (`/admin/audit-logs`) | Work (review the audit trail) | Sidebar - Oversight |
| Account / Profile (Account modal) | Setting (personal) | Hub Personal - Account |
| Notifications preferences (Account modal) | Setting (personal) | Hub Personal - Notifications |
| **Email + E-signature connect (Organization panes, per-user)** | **Setting (personal connection)** | **Hub Personal - Email & E-signature** |
| Email Templates (`/email-templates`, orphan) | Setting (personal + shared) | Hub Personal - Email Templates |
| My Checklist Templates / Tagged Notes / Preferred Vendors / Internal Resources (Account modal) | Setting (personal) | Hub Personal - My Playbook |
| Help & tour (Account modal) | Setting (personal) | Hub Personal - Help & Tour |
| Company (Organization) | Setting (workspace) | Hub Workspace - Company |
| Branding (Organization) | Setting (workspace) | Hub Workspace - Branding |
| Billing & credits (Organization) | Setting (workspace) | Hub Workspace - Billing & Credits |
| Users & invites (`/admin/users`) | Setting (workspace - access admin) | Hub Workspace - Users & Invites |
| Teams (`/admin/teams`) | Setting (workspace) | Hub Workspace - Teams |
| Task Templates (`/admin/task-templates`) | Setting (workspace - intake library) | Hub Workspace - Task Templates |
| Vendor Templates (`/admin/vendor-templates`) | Setting (workspace - comms library) | Hub Workspace - Vendor Templates |
| Team Playbook (`/admin/team-settings`) | Setting (workspace) | Hub Workspace - Team Playbook |
| Integrations / webhooks (`/admin/integrations`, tenant CRM) | Setting (workspace - connections) | Hub Workspace - Integrations & Webhooks |
| AI configuration (Organization stub) + AI Governance (`/admin/confidence`) | Setting (workspace) - **merge into one** | Hub Workspace - AI & Automation |
| Payment Access (`/admin/payment-access`) | Setting (workspace) | Hub Workspace - Payment Access |
| Advertising (`/admin/advertising`) | Setting (workspace) | Hub Workspace - Advertising |
| Delete organization (Organization danger) | Setting (workspace - owner only) | Hub Workspace - Delete Organization |

Result: the sidebar holds only work and record-review; per-user connections sit with the user in Personal Settings; tenant config sits in Workspace Settings; the Owner block and the avatar "Organization" entry disappear because the hub makes them redundant.

---

## 4. ListedKit reference analysis (what I am matching)

From the two screenshots and help.listedkit.com:

- **Entry point.** Settings opens from the **avatar menu at the bottom-left** ("Invite a friend / Settings / Logout"). It is not a sidebar work item. The work sidebar (Dashboard, Contacts, Transactions with Active Listing / Under Contract / Closed / Void) stays untouched when you open Settings.
- **Hub layout.** A full page with two section headers: **Personal Settings** then **Admin Settings**. Each is a responsive grid of cards (three columns on desktop). Each card is an **icon + bold title + one-sentence description**, and the whole card is clickable.
- **Search.** A "Search settings..." input sits above the grid for find-by-typing, on top of click-to-find.
- **Personal cards (ListedKit):** Account, Email, Notifications, Task Templates, Commands, Compliance, Intake Preferences, Calendar, Rules, Ava Approvals, Ava SMS, Integrations, Form Library, Summary Design.
- **Admin cards (ListedKit):** Users, Billing, Company.
- **Detail page.** A card opens a focused page with a breadcrumb "**< Settings / Account**" and the controls for just that area (the Account detail shows avatar upload, name, email, role, display toggles, voice settings, and an Active Sessions table).

I am replicating the **structure** (avatar-menu entry, two-group card grid, search box, breadcrumbed detail pages) and adapting the **card set** to Velvet Elves' actual features. I am not copying ListedKit cards VE has no backend for (Commands, Ava SMS, Ava Voice, Form Library, Summary Design, Rules); empty shells would violate the no-demo-data rule. ListedKit's "Email" personal card maps to VE's two real personal email surfaces: **Email & E-signature** (connect your inbox + DocuSign) and **Email Templates**.

---

## 5. Target information architecture

### 5.1 Internal sidebar after the change (work only)

```
Dashboard

DEALS
  Active Transactions      (badge)
  Pending                  (badge)
  Closed
  All Transactions
  Clients

WORKFLOW
  My Task Queue            (badge)
  All Documents
  Closing Calendar

PAYMENTS
  Invoices & Payments
  Commission Payouts       (only if user can trigger payouts)

VENDORS
  Vendor Directory

INTELLIGENCE
  AI Suggestions
  AI Email Review          (badge)
  Vendor Proposals         (badge)
  Analytics

TEAM            (TeamLead + Admin)
  Team Overview

OVERSIGHT       (Admin)
  Communication Audit
  Audit Log

[ footer ]
  + New Transaction (CTA)
  User card -> menu: Settings, Log out
```

What changed in the sidebar:

- The **Team** group drops Teams, Team Members, Task Templates, Vendor Templates, and Team Settings (all moved to the hub). It keeps only **Team Overview**, the roster + performance review surface.
- The **Admin** group is renamed **Oversight** and keeps only the two record-review surfaces (Communication Audit, Audit Log). Everything else it held (AI Governance, Payment Access, Integrations, Advertising) moves to the hub. It still renders for Admin only (the same audience the old Admin group had).
- The **Workspace owner** block is removed. It was a redundant subset of shortcuts; removing it does **not** reduce the owner's reach, because both route guards already grant the owner a bypass (Section 16, F2). The owner now reaches the same surfaces through the hub, the same way every admin does.
- The avatar menu (both the sidebar-footer copy and the topbar copy) becomes **Settings** + **Log out**; the "Account" and "Organization" entries collapse into the single Settings entry. Per the Shared Shell spec this is what the menu was always meant to be.
- Critically, an Agent / TC still reaches **their own inbox + DocuSign connection** after this change, because Email & E-signature is a Personal hub card (5.2), not the removed Organization page. No AI-email workflow is stranded.

Attorney keeps its Workspace + Intelligence sidebar groups unchanged and gains the same avatar-menu Settings entry, showing the personal cards it is entitled to (Account, Notifications, Email & E-signature, My Playbook, Help - not Email Templates, which its route excludes).

### 5.2 The Settings hub (`/settings`) - the one place

A full page, opened from the avatar-menu **Settings** entry. Card grid, two groups, search box on top. Cards are role-filtered so a user only sees cards they can actually use.

**Personal Settings** (every internal role; per-user scope):

| Card | Description (one line, on the card) | Routes to | Source today |
| --- | --- | --- | --- |
| Account | Update your profile, signature, and display preferences. | `/settings/account` | `ProfileSection` (Account modal) |
| Notifications | Choose which reminders and assignment alerts you receive. | `/settings/notifications` | `NotificationsSection` |
| Email & E-signature | Connect your inbox (Gmail / Outlook) and DocuSign. | `/settings/connections` | Email + E-sign panes lifted out of OrganizationPage |
| Email Templates | Create reusable email templates and your signature. | `/settings/email-templates` | `EmailTemplatesPage` (orphan today; excludes Attorney) |
| My Playbook | Your personal closing checklist, tagged notes, preferred vendors, and resources. | `/settings/my-playbook` | `PersonalSections` (4 panes) |
| Help & Tour | Replay the guided tour and reach support. | `/settings/help` | `HelpSection` |

**Workspace Settings** (gated; see the matrix in 5.3; tenant scope):

| Card | Description | Routes to | Source today |
| --- | --- | --- | --- |
| Company | Your brokerage name, plan, and seats. | `/organization?section=company` | Organization page |
| Branding | Logo, brand color, and display name across the app. | `/organization?section=branding` | Organization page |
| Billing & Credits | Credit balance, purchases, and payment history. | `/organization?section=billing` | Organization page (flag-gated) |
| Users & Invites | Invite members, assign roles, and manage access. | `/admin/users` | AdminUsersListPage |
| Teams | Create teams and assign leads and members. | `/admin/teams` | AdminTeamsPage |
| Task Templates | Reusable task checklists applied to new transactions. | `/admin/task-templates` | TaskTemplateListPage |
| Vendor Templates | Standard vendor outreach emails the AI can send. | `/admin/vendor-templates` | VendorTemplatesPage |
| Team Playbook | The team's shared checklist, notes, vendors, and resources. | `/admin/team-settings` | AdminTeamSettingsPage |
| Integrations & Webhooks | Connect your CRM and other tools via webhooks. | `/admin/integrations` | AdminIntegrationsPage |
| AI & Automation | AI provider, confidence thresholds, and auto-send rules. | `/admin/confidence` | AdminAIGovernancePage (canonical) |
| Payment Access | Choose which roles can invoice, refund, or pay out. | `/admin/payment-access` | AdminPaymentAccessPage |
| Advertising | Control sponsored placements and your house ads. | `/admin/advertising` | AdminAdvertisingPage |
| Delete Organization | Permanently delete this workspace. | `/organization?section=danger` | DangerZone (owner / platform admin only) |

Three deliberate consolidations are baked into this table:

- **Per-user connections become Personal.** Email + E-signature (each user's own Gmail/Outlook + DocuSign) leave the tenant Organization page and become the Personal "Email & E-signature" card, available to every internal role. The Organization page is then purely tenant config (Company, Branding, Billing, Delete), which is the only thing it should ever have been.
- **AI configuration is now one surface.** The Organization "AI configuration" stub pane (non-persistent toggles) is retired; real AI config lives on the AI Governance page (the "AI & Automation" card), satisfying Style Guide 16.8. The Admin dashboard's existing "Tune thresholds ->" deep link keeps working because the route is unchanged; only its breadcrumb root changes to "Settings".
- **Connections read as two honest cards in two scopes.** Personal "Email & E-signature" is your own accounts; Workspace "Integrations & Webhooks" is the tenant's outbound CRM webhooks. Genuinely different jobs in different scopes, so two cards.

**Platform Settings** (platform admins only; a third hub group). The vendor-side fleet console splits by the same work-vs-settings rule: the **Tenants** fleet console and the cross-tenant **AI usage** report stay in the sidebar's Platform group (platform-admin work / reporting), while the two configuration surfaces move into a hub "Platform" group:

| Card | Description | Routes to | Source today |
| --- | --- | --- | --- |
| Platform Billing | Credit packs, pricing, and platform billing health. | `/platform/billing` | PlatformBillingPage |
| Platform Advertising | Ad packages, creative approvals, and global performance. | `/platform/advertising` | PlatformAdvertisingPage |

Both cards are gated to `is_platform_admin` (mirroring `PlatformAdminGuard`), so they never 404. Their breadcrumbs root at Settings; Tenants and AI usage keep the plain "Platform" crumb.

Note on Notifications: the **bell** in the topbar still opens the live notification feed (work); the Settings "Notifications" card configures which notifications you receive (preferences). They are deliberately different surfaces and must not be conflated.

### 5.3 Role visibility matrix for the hub

A card renders only if the role can reach its destination. Columns are by role; the **Owner** column is the non-Admin tenant owner, whose `is_tenant_owner` flag grants a bypass on every guarded route (verified in `ProtectedRoute` F1 and `RoleRoute` F2).

| Card | Agent / TC | Attorney | TeamLead | Admin | Owner |
| --- | --- | --- | --- | --- | --- |
| Account | yes | yes | yes | yes | yes |
| Notifications | yes | yes | yes | yes | yes |
| Email & E-signature | yes | yes | yes | yes | yes |
| Email Templates | yes | **no** | yes | yes | yes [c] |
| My Playbook | yes | yes | yes | yes | yes |
| Help & Tour | yes | yes | yes | yes | yes |
| Company | - | - | - | edit | view [a] |
| Branding | - | - | - | edit | view [a] |
| Billing & Credits [b] | - | - | - | yes | yes |
| Users & Invites | - | - | yes | yes | yes |
| Teams | - | - | - | yes | yes |
| Task Templates | - | - | yes | yes | yes |
| Vendor Templates | - | - | yes | yes | yes |
| Team Playbook | - | - | yes | yes | yes |
| Integrations & Webhooks | - | - | - | yes | yes |
| AI & Automation | - | - | - | yes | yes |
| Payment Access | - | - | - | yes | yes |
| Advertising | - | - | - | yes | yes |
| Delete Organization | - | - | - | owner-only [d] | yes |

Footnotes:
- **[a]** Company and Branding render for the Owner but editing requires the Admin role (`canEditTenant = hasMinimumRole(role, 'Admin')`), so a non-Admin owner sees them read-only. The page already enforces this; the card just surfaces the page.
- **[b]** The Billing & Credits card shows only when the credit-billing flag is on (the wallet probe used by OrganizationPage succeeds). When the flag is off, the card is hidden for everyone - no dead card.
- **[c]** Email Templates follows its exact route allow-list (Agent / TC / TeamLead / Admin); an owner whose role is Attorney would not see it.
- **[d]** Delete Organization shows only to the workspace owner or a platform admin (`canSeeDanger`), so an Admin who is not the owner does **not** see it.

Rules captured by the matrix:
- Agent / TC and Attorney see **only the Personal Settings group**; the "Workspace Settings" header does not render for them at all (no empty section).
- TeamLead adds the four team-management cards (Users & Invites, Task Templates, Vendor Templates, Team Playbook). These mirror the four `/admin/*` routes guarded at `requiredRole="TeamLead"`. Teams stays Admin/Owner because, although its route allows TeamLead, the product intent (and the current nav) treats team structuring as Admin governance.
- Admin and Owner see the full Workspace group. The matrix never offers a card whose route would reject the user, so a tester never lands on `/unauthorized`.
- This intentionally narrows one thing relative to today: Company / Branding / Billing and the per-user connections were all reachable by any internal role via the avatar "Organization" entry. After the change, tenant config is Admin/Owner only (standard), while the per-user connections move to the Personal card every internal role keeps. No backend gate changes, and every old URL still resolves (Section 10), so nothing breaks; the casual Agent simply stops seeing brokerage config they could not edit.

### 5.4 Portal roles (Client / FSBO / Vendor)

Portal users keep the **existing Account modal** unchanged; their avatar menu continues to open it. Their settings are trivial (Client / Vendor: identity only; FSBO: identity + a Preferences pane), the modal works today, and their shells (`ClientWorkspaceLayout`, `VendorWorkspaceLayout`) are bespoke. A full hub for two or three controls would add risk for no benefit - settings depth should match the surface. The `/client/settings` and `/fsbo/settings` routes (which call `OpenAccountModalRoute`) are untouched.

---

## 6. The detail-page contract

Every card lands on a focused detail surface that obeys one contract:

1. **Breadcrumb roots at Settings.** The top crumb is "Settings" (linking to `/settings`), then the area name, exactly like ListedKit's "< Settings / Account". This replaces today's mixed roots ("Organization >", "Team >", "Admin >").
2. **It reuses the existing page wherever one exists.** Most destinations already exist (Organization page, the admin pages, EmailTemplatesPage, AdminTeamSettingsPage). The work is re-pointing the entry, changing the breadcrumb root, and removing the old sidebar link - not rebuilding the page. The genuinely new pages are the hub landing and the lifted personal panes (Account, Notifications, Email & E-signature, My Playbook, Help).
3. **The page owns its own scroll.** Per the recurring rule (`App pages own their scroll`): outer `flex h-full min-h-0 flex-col overflow-hidden bg-ve-bg`, header `shrink-0`, body `flex-1 min-h-0 overflow-y-auto`. The existing Organization and Team Settings pages already do this; the new pages must too.
4. **Back returns to the hub.** The "Settings" crumb and the browser back button both return to `/settings` with the search query preserved.
5. **Modal-era panes adapt cleanly.** The personal panes that take a `closeModal` callback today (`ChecklistTemplatesSection`, `HelpSection`) get a navigate-back handler instead when hosted as pages. The Account modal stays mounted only for portal roles; internal roles no longer open it.

---

## 7. The hub landing page - detailed design

A new page component, `SettingsHubPage`, rendered at `/settings` inside `AppLayout` for internal roles.

### 7.1 Anatomy

```
+ ---------------------------------------------------------------- +
| Settings                                                         |  <- header (serif title, no breadcrumb; this is the IA root)
| [ Search settings...                              ]              |  <- search input
+ ---------------------------------------------------------------- +
| PERSONAL SETTINGS                                                |  <- mono kicker group label
|  [Account]            [Notifications]      [Email & E-signature] |
|  [Email Templates]    [My Playbook]        [Help & Tour]         |
|                                                                  |
| WORKSPACE SETTINGS                                               |  <- renders only if the role has >=1 workspace card
|  [Company]            [Branding]           [Billing & Credits]   |
|  [Users & Invites]    [Teams]              [Task Templates]      |
|  [Vendor Templates]   [Team Playbook]      [Integrations]        |
|  [AI & Automation]    [Payment Access]     [Advertising]         |
|  [Delete Organization]                                           |
+ ---------------------------------------------------------------- +
```

### 7.2 Card spec (matches the Style Guide card vocabulary)

- Container `rounded-xl border border-ve-border bg-white shadow-soft`; hover lifts with `shadow-card-hover` + `-translate-y-[1px]`, 150ms ease-out (Style Guide 5.3, 8). The whole card is one `<Link>` (one click target, no nested differing actions, per anti-pattern 6 and 16.5).
- Padding `p-5` (4.2).
- Layout: a tinted circular icon tile (~40px, `lucide-react` icon in champagne on `ve-orange-soft`), then a **serif title** (`font-serif text-[16px]`) and a **one-line description** (`text-[13.5px] text-ve-text-secondary`, never below the 12px floor).
- Delete Organization uses the red triad (`ve-red-bg` / `ve-red-border` / `ve-red-text`) and sits last, set apart, so a destructive action never reads like a routine card.
- Grid `grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4`. Group label is a mono kicker (`font-mono text-[12px] tracking-[1.5px] uppercase text-ve-orange`).

### 7.3 Search behavior (mouse-first, typing optional)

- Client-side filter over each card's title, description, and a small hidden keyword list (so "email" surfaces Email & E-signature + Email Templates; "invoice" surfaces Payment Access + Billing; "docusign" surfaces Email & E-signature).
- Filtering hides non-matching cards live; an empty result shows an explanatory empty state ("No settings match 'xyz'."), never a blank page.
- Search is a convenience on top of click-to-find; nothing requires the keyboard.

### 7.4 Shell, header, mobile

- Canonical page shell (15.1); page owns its scroll.
- Header: serif "Settings" title; as the IA root it carries no breadcrumb (its children do). Gutter `px-3 md:px-6`, no `max-w` cap on the grid (15.3).
- Mobile: grid collapses to one column; cards stay full-width tap targets (>= 48px, 12).

---

## 8. Style Guide compliance checklist

| Rule | How the hub honors it |
| --- | --- |
| Three-voice type | Mono kickers for group labels, serif card titles, sans descriptions (3.2). |
| Comfort scale v2 | Descriptions 13.5px, kickers 12px, nothing below 12px (v2.1). |
| `ve-*` tokens only | No raw hex; champagne from `ve-orange*`, status triads paired (2.1-2.4). |
| Card vocabulary | One card shell for every hub card; variation only by tone (16.2). |
| Shadows | `shadow-soft` rest, `shadow-card-hover` hover; no `shadow-2xl` (5.3). |
| Icons | `lucide-react`, `h-5 w-5` in the icon tile (7). |
| Motion | 150ms ease-out hover, no bounce (8, v2.4). |
| Page shell + scroll | Canonical shell, page owns scroll, `px-3 md:px-6`, no `max-w` (15.1, 15.3). |
| Breadcrumb pattern | Detail pages root the crumb at "Settings" using the shared header anatomy (15.2). |
| Empty states | Search-empty and read-only states are explanatory, not apologetic (11). |
| Destructive treatment | Delete Organization uses the red triad and is set apart; no native confirms (6.5, 13.5). |

---

## 9. Implementation phases (no code in this plan - file touch-list only)

Each phase ends green (frontend `tsc` + `eslint` + tests) and is independently testable in the UI. No commits (Jan commits).

### Phase 0 - Route constants
- Add to `src/utils/constants.ts`: `SETTINGS_ACCOUNT`, `SETTINGS_NOTIFICATIONS`, `SETTINGS_CONNECTIONS`, `SETTINGS_EMAIL_TEMPLATES`, `SETTINGS_MY_PLAYBOOK`, `SETTINGS_HELP` (`SETTINGS` = `/settings` already exists). No behavior change.

### Phase 1 - Settings hub landing + the /settings role split
- New `src/pages/settings/SettingsHubPage.tsx` (card grid, two groups, search, role-filtered per 5.3).
- New `src/pages/settings/settingsCards.ts` - the card registry (id, title, description, icon, route, keyword list, visibility predicate). One source of truth for the grid, search, and tests.
- New `src/pages/settings/SettingsRouter.tsx` for `/settings`: renders `SettingsHubPage` for internal roles and falls back to `OpenAccountModalRoute` (the existing modal behavior) for portal roles, so a portal user never lands on the internal hub. Wire it in `App.tsx`.
- After Phase 1, every card deep-links to its existing destination; nothing is removed yet, so there is no regression window.

### Phase 2 - Lift the personal panes into breadcrumbed pages
- New pages wrapping existing components, each with the Settings-rooted breadcrumb and self-owned scroll:
  - `SettingsAccountPage` wraps `ProfileSection`.
  - `SettingsNotificationsPage` wraps `NotificationsSection`.
  - `SettingsConnectionsPage` renders the Email provider rows + DocuSign pane, reusing the existing `ProviderRow`, the `useEmailProviderOAuth` / `useListIntegrations` / `useDisconnectIntegration` hooks, and `ConnectEsignWizardModal` - the same code OrganizationPage uses today. This is per-user, so it is available to every internal role.
  - `SettingsMyPlaybookPage` wraps the four `PersonalSections` panes as a section rail (mirrors AdminTeamSettingsPage's rail + pane), with `closeModal` replaced by a navigate-back handler.
  - `SettingsHelpPage` wraps `HelpSection` (it sits inside `AppLayout`, which is inside `TourProvider`, so `useTour().start()` still works), with the same `closeModal` adaptation.
  - Give `EmailTemplatesPage` the Settings breadcrumb (it is already a full page).
- Register the detail routes in `App.tsx` for internal roles. Attorney is allowed on Account / Notifications / Connections / My Playbook / Help, but Email Templates keeps its existing allow-list that excludes Attorney.
- Point the hub's personal cards at these routes.

### Phase 3 - Re-root the workspace pages at Settings, and de-bundle the Organization page
- `OrganizationPage`: change the breadcrumb root from "Organization" to "Settings"; remove its `integrations` (Email) and `esign` sections (moved to the personal Connections page) and its `ai` stub section (retired). The page keeps Company, Branding, Billing, and Danger.
- `AdminPageHeader`: add an optional crumb-root prop (label + link) so a page can root at "Settings" instead of the hard-coded "Admin / admin dashboard".
  - Pass "Settings" root on the four pages that move into the hub: AI Governance (`/admin/confidence`), Advertising, Integrations, Payment Access.
  - Keep an "Oversight" root on Audit Log (and update Communication Audit's inline header likewise) since those stay in the sidebar.
- Inline-header pages that move to the hub get their root crumb changed to "Settings": `AdminTeamSettingsPage` (was "Team"), `AdminUsersListPage`, `AdminTeamsPage`, `TaskTemplateListPage`, `VendorTemplatesPage`, `EmailTemplatesPage`. Where a list page has no breadcrumb today, add the shared header so the group reads as one surface.
- No route changes here; only breadcrumb roots and the removed Organization sections.

### Phase 4 - Strip settings out of the sidebar
- `src/layouts/AppLayout.tsx` `buildSection`:
  - `team` case: keep only Team Overview.
  - `admin` case: rename the label to "Oversight"; keep only Communication Audit + Audit Log.
  - remove the "Workspace owner" block (`showOwnerSection`, `ownerNavItems`) - reach is preserved by the owner bypass + the hub.
  - avatar menu (both the sidebar-footer copy and the topbar copy): replace "Account" + "Organization" with a single **Settings** item navigating to `/settings`; keep "Log out".
- `src/layouts/dashboardShellConfig.ts`: the `settings` section key resolves to `null` in `buildSection`, so no sidebar group renders for it - no reshuffle needed beyond the `team`/`admin` content above. Verify each role still lists `team`/`admin` only where intended.

### Phase 5 - Cleanup, redirects, docs
- Keep every existing `/admin/*` and `/organization` route resolving (no broken bookmarks); optionally add redirects so old deep links land with the new breadcrumb.
- Retire `OpenAccountModalRoute` for internal roles (portals keep it via `SettingsRouter`). Remove the dead Owner-block code and the Organization avatar entry.
- Docs: update `FRONTEND_UI_WORKFLOW_LOGIC.md` Shared Shell (avatar menu = Settings, Log out; sidebar groups = Deals / Workflow / Payments / Vendors / Intelligence / Team / Oversight; Email + DocuSign connect now in Settings > Email & E-signature) and Section 10 Admin; add a "Settings IA" note to `SYSTEM_DESIGN.md` capturing the Section 2 rule.

### Phase 6 - Polish and screenshot gate
- Render the hub and three representative detail pages headless; screenshot per role (Admin, TeamLead, Agent, Attorney) and compare against this plan + the ListedKit reference before handing screenshots to Jake.

---

## 10. Routing and back-compatibility

- `/settings` becomes the role-split router (internal hub / portal modal). `/settings/*` are the new personal detail pages.
- All `/organization` and `/admin/*` routes are unchanged, so every existing bookmark, redirect, and dashboard deep link keeps working; only their breadcrumb root and sidebar entry change. (The Organization page drops three sub-sections, but `?section=integrations` / `esign` / `ai` links can redirect to the new Connections page / AI Governance page so old links still land somewhere correct.)
- `/email-templates` keeps its route and gains a hub card + breadcrumb (it stops being an orphan).
- Portal `/client/settings`, `/fsbo/settings` continue to open the Account modal.
- No backend route or authorization change anywhere.

---

## 11. Resolved decisions (each chosen as the most standard option)

- **D1 - Communication Audit + Audit Log: sidebar, not Settings.** Settings stays purely configuration; these are record-review surfaces, so they live in a slim Admin-only "Oversight" sidebar group. This matches the Style Guide's framing of them as dashboard-adjacent admin pages and the prior nav plan that placed Communication Audit in the Admin group. ListedKit's "Compliance" card is compliance *configuration*, not an audit feed, so there is no conflict.
- **D2 - Hide Workspace Settings from Agent / TC (and Attorney).** Regular members see only Personal Settings, exactly as ListedKit and mainstream SaaS do. The "Workspace Settings" header does not render for them.
- **D3 - Avatar menu = Settings + Log out.** One clean entry to all settings; the "Invite a friend" referral can be added later if that feature is built.
- **D4 - Portals keep the Account modal.** Settings depth matches the surface; a one-to-three-control modal is the standard lightweight pattern and avoids rebuilding bespoke portal shells.
- **D5 - One "My Playbook" card + a separate "Email Templates" card.** The four personal playbook editors are grouped into one card (mirroring the team Playbook), while Email Templates stays its own card because it is a distinct, frequently used surface (and ListedKit lists "Email" separately).

---

## 12. Non-goals and risks

- **Non-goals:** changing any page's internal functionality, changing backend authorization, redesigning dashboards, or migrating `/admin/*` URLs (labels and grouping carry the IA; URLs can lag, as the prior nav plan decided).
- **Risk - a power user who memorized the old sidebar path.** Mitigation: the hub search box plus preserved URLs mean every old deep link still resolves, and avatar > Settings is one click from anywhere.
- **Risk - a wall of cards for a full Admin.** Mitigation: role filtering means most users see five or six cards; only Admin/Owner see the long list, and the two-group split + search keep it scannable.
- **Risk - de-bundling the Organization page (moving Email/E-sign out) regresses the connect flow.** Mitigation: the Connections page reuses the exact same components and hooks; Phase 2 ships it before Phase 3 removes the panes, and `?section=integrations` links redirect to it.
- **Risk - breadcrumb inconsistency mid-rollout.** Mitigation: Phase 3 re-roots all detail breadcrumbs in one pass; the hub ships in Phase 1 already pointing at working destinations.

---

## 13. Relationship to the earlier `NAVIGATION_TEAM_ADMIN_REORG_PLAN`

That plan (2026-05-20) cleaned up the Team-vs-Admin split inside the sidebar and removed a duplicate Users link. It left tenant configuration reachable from a footer/avatar link and deferred URL migration. This plan:

- **Supersedes** the part that kept configuration reachable from the sidebar/footer: all configuration now lives in the single hub and leaves the sidebar.
- **Keeps** its categorization discipline (place by purpose and access tier), its decision not to migrate `/admin/*` URLs, and its rule that no nav item points to an unbuilt route.

---

## 14. UI testing guide for non-developer testers

Mouse-only except where it says to type. No dev tools needed. One script per role.

### 14.1 Admin (use an account that is also the workspace owner for the last step)
1. Sign in. The left sidebar shows **Deals, Workflow, Payments, Vendors, Intelligence, Team (Team Overview only), Oversight (Communication Audit, Audit Log)** and **no** Task Templates / Team Settings / Integrations / Advertising in the sidebar.
2. Click the avatar (bottom-left). The menu shows **Settings** and **Log out** only.
3. Click **Settings**. A page titled "Settings" shows two groups: **Personal Settings** and **Workspace Settings**, as cards.
4. Personal > **Account**: breadcrumb reads "Settings / Account", profile loads; click "Settings" to return.
5. Personal > **Email & E-signature**: confirm you can see Gmail / Outlook / DocuSign connect rows. Return.
6. Personal > **Email Templates**: confirm it opens (was unreachable before). Return.
7. Workspace > **Company**, return; **Branding**, return; **Users & Invites**, return; **AI & Automation**, return. Each loads with a "Settings / ..." breadcrumb, no error.
8. Confirm **AI is configured in one place only**: the old Organization "AI configuration" pane is gone; AI lives on the AI & Automation card.
9. Confirm **Delete Organization** appears last, in red, set apart - only because you are the owner.
10. Type "email" in the search box: only **Email & E-signature** and **Email Templates** remain. Clear it; all cards return.

### 14.2 Team Lead
1. Sidebar shows the work groups plus **Team (Team Overview)**; no Oversight group.
2. Open **Settings**. Workspace Settings shows **Users & Invites, Task Templates, Vendor Templates, Team Playbook** and **not** Company, Branding, Billing, Teams, Integrations, AI & Automation, Payment Access, Advertising, or Delete Organization.
3. Open **Team Playbook**: loads with the team picker and a "Settings / ..." breadcrumb.

### 14.3 Agent / Transaction Coordinator
1. Open **Settings**. Only the **Personal Settings** group renders (Account, Notifications, Email & E-signature, Email Templates, My Playbook, Help & Tour); there is **no** Workspace Settings header.
2. Open **Email & E-signature** and confirm you can start connecting your own Gmail/Outlook inbox (this is the path the AI-email workflow depends on - it must be reachable here).
3. Open **My Playbook**: the four personal sections (checklist, notes, vendors, resources) are reachable as a rail and save without error.

### 14.4 Attorney
1. Sidebar Workspace + Intelligence groups unchanged. Open **Settings**: Personal cards only, and specifically **Account, Notifications, Email & E-signature, My Playbook, Help & Tour** - confirm there is **no Email Templates card** (the route excludes Attorney).

### 14.5 Client / FSBO / Vendor (portal)
1. Sign in as each. The avatar menu still opens the lightweight **Account** modal (Profile; FSBO also Preferences). Confirm nothing about portal navigation changed.

### 14.6 Cross-cutting (any role)
- No hub card leads to an "unauthorized" page (role filtering works).
- Every detail page scrolls to its bottom control without clipping (page-owns-scroll).
- Browser back from any detail page returns to the hub.
- Old bookmarks load with a "Settings" breadcrumb: `/organization`, `/admin/users`, `/email-templates`, and `/organization?section=integrations` (which now lands on the Email & E-signature connections page).

---

## 15. Acceptance criteria

- [ ] There is exactly one entry to settings: the avatar-menu **Settings** item. "Account", "Organization", and the "Workspace owner" block are gone.
- [ ] The sidebar contains only work and record-review surfaces; no configuration item remains in it.
- [ ] The hub shows two groups (Personal, Workspace) of clickable cards, role-filtered per 5.3 so no card leads to `/unauthorized`.
- [ ] **Every internal role (including Agent / TC / Attorney) can connect their own inbox + DocuSign from Settings > Email & E-signature** - the AI-email workflow is never stranded.
- [ ] Every former settings surface is reachable from exactly one card; none is duplicated, and Email Templates is no longer orphaned.
- [ ] AI is configured on one surface only; the Organization page no longer hosts Email, E-signature, or an AI pane.
- [ ] Every detail page breadcrumbs back to "Settings", owns its scroll, and uses the `ve-*` tokens and card vocabulary.
- [ ] Search filters cards live and shows an explanatory empty state.
- [ ] All existing `/organization` and `/admin/*` URLs still resolve; `?section=integrations/esign/ai` redirect to the new homes; no backend authorization changed.
- [ ] `tsc`, `eslint`, and the frontend test suite are green.
- [ ] Per-role screenshots match this plan and the ListedKit reference before Jake review.

---

## 16. Review log - flaws found in rev 1 and corrected here

I re-read the live source specifically to find workflow/logic errors. The fixes folded into this rev:

- **F1 - Email + E-signature are per-user, not tenant settings (highest-impact fix).** `integrations.py` uses `get_current_user` and stores tokens on the user's row for connect / list / disconnect / OAuth-begin / send; `useIntegrations.ts` matches; onboarding tells users to "connect Gmail / DocuSign later from Settings". Rev 1 folded these into the Admin-only Organization page, which would have **stranded every non-Admin agent's inbox connection and broken AI email** for them. Corrected: Email & E-signature is a **Personal** card available to all internal roles, lifted out of the Organization page into a dedicated per-user Connections page.
- **F2 - Workspace-owner bypass.** Both `ProtectedRoute` (F1 clause) and `RoleRoute` (`ownerBypass`) let `is_tenant_owner` through guarded routes. Rev 1 claimed the Owner block gave the owner "exactly four things" and would lose nothing; in fact the owner already reaches every admin surface. Corrected: the Owner column in 5.3 mirrors Admin (full Workspace group), and 5.1 explains the block's removal does not reduce reach.
- **F3 - Email Templates excludes Attorney.** The `/email-templates` route allow-list is Agent / TC / TeamLead / Admin. Rev 1 listed Email Templates for Attorney (matrix, Attorney note, Phase 2, test 14.4). Corrected everywhere: Attorney has no Email Templates card.
- **F4 - `/settings` is shared with portals.** `/settings` currently maps to `OpenAccountModalRoute`, which portals also use. Rev 1 would have rendered the internal hub for a portal user hitting `/settings`. Corrected: a `SettingsRouter` renders the hub for internal roles and the modal behavior for portal roles.
- **F5 - Breadcrumb re-rooting is not a one-line prop change.** Only five admin pages use `AdminPageHeader`, and it hard-codes an "Admin -> admin dashboard" crumb; the rest (Organization, Team Settings, Communication Audit, list pages) use inline headers. Corrected: Phase 3 adds an optional crumb-root prop to `AdminPageHeader` and enumerates exactly which pages root at "Settings" vs stay "Oversight", plus the inline-header edits.
- **F6 - Company / Branding / Billing were reachable by all internal roles** via the avatar "Organization" entry. Rev 1 implied this was already Admin-only. Corrected: 5.3 states the deliberate (frontend-only) narrowing to Admin/Owner, with old URLs still resolving so nothing breaks.
- **F7 - Notifications ambiguity.** Clarified that the topbar bell (live feed, work) and the Settings Notifications card (preferences) are different surfaces.
- **F8 - Help & My Playbook modal callbacks.** Noted that panes taking `closeModal` need a navigate-back adaptation when hosted as pages, and that `SettingsHelpPage` stays inside `TourProvider` so tour replay still works.

---

*End of plan. This document is plan-only; no source was changed in producing it.*
