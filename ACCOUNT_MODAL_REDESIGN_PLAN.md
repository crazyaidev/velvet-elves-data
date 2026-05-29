# Account Modal + Organization Page — Settings Redesign & M5.3 Redundancy Cleanup

| | |
| --- | --- |
| **Status** | **Implemented (2026-05-29).** All four phases shipped to the frontend working tree; `tsc -p tsconfig.app.json --noEmit` and `eslint` are clean. See §0 Implementation status for the as-built notes and the two intentional deviations. |
| **Date** | 2026-05-29 |
| **Scope** | Frontend only. Re-composes the existing Profile modal + Settings page + Client/FSBO settings pages into (1) a shared **Account modal** and (2) an internal **Organization page**; and eliminates the M5.3 navigation/Settings redundancies. No backend, no DB, no portal-shell or page-content rewrites beyond those listed. |
| **Goal** | One home per concept: **identity + personal preferences** live in the Account modal; **tenant/workspace configuration** lives on the Organization page; **team playbook** (Task/Vendor Templates, team checklist/notes/vendors/resources) lives in the Team/Admin groups; **per-deal work** stays where it is. Remove every duplicate/echoed destination. |
| **Decisions captured** | (D1) Modal scope = **Account modal (identity + personal prefs) + separate Organization page** for tenant config. (D2) Routing = **keep `/settings`, `/client/settings`, `/fsbo/settings` (+ `?section=`)** as URLs that auto-open the modal. (D3) Task Templates = **removed entirely** from Settings/Organization (no link-out); canonical home stays `/admin/task-templates`. (D4) Brokerage Overview = **merged into** Team Overview. |
| **Supersedes / reverses** | M5.3 **v2.1** decision that made Profile a standalone modal *and* kept Settings a full page. This plan folds Profile *into* Settings and turns the combined personal surface into the modal. Doc sync required (see §13). |
| **Authoritative sources** | `MILESTONE_5_3_IMPLEMENTATION_PLAN.md` §0.2 (three-surface model), §3.2 (frontend current state), §6.B–6.F, §12 (acceptance) · `NAVIGATION_TEAM_ADMIN_REORG_PLAN.md` §5 (Team-vs-Admin rule), §8.4 (Task Templates de-dup) · `FRONTEND_UI_WORKFLOW_LOGIC.md` §6.3 (Settings as-built), §10 (Admin section), §11.1 (Profile) · `STYLE_GUIDE.md` §6.5 (Dialog), §15.2 (AdminPageHeader), §16.1 |
| **Visual-consistency anchors** | `components/profile/ProfileModal.tsx` (identity body) · `pages/settings/SettingsPage.tsx` (section-rail + work-pane layout, editorial primitives) · `components/profile/M53Editors.tsx` + `hooks/useM53Settings.ts` (shared editors/hooks — reused, not rewritten) · `components/ui/dialog.tsx` (Radix Dialog host) |

---

## 0. Implementation status (2026-05-29)

All four phases are implemented in `velvet-elves-frontend`. `tsc` and `eslint` pass.

**New files:** `contexts/AccountModalContext.tsx` · `components/account/AccountModal.tsx` · `components/account/sections/{primitives,ProfileSection,PersonalSections,PortalSections}.tsx` · `pages/organization/OrganizationPage.tsx` · `pages/settings/OpenAccountModalRoute.tsx`.

**Deleted:** `components/profile/ProfileModal.tsx` · `contexts/ProfileModalContext.tsx` · `pages/settings/SettingsPage.tsx` · `pages/client/ClientSettingsPage.tsx` · `pages/fsbo/FsboSettingsPage.tsx` · `pages/admin/AdminBrokerageOverviewPage.tsx`.

**Changed:** `App.tsx` (provider/modal mount, routes, `/organization`) · `layouts/AppLayout.tsx` (avatar menus → Account + Organization, footer gear opens modal, Admin group split into **Team Config** + **Admin**, Brokerage entry removed) · `layouts/dashboardShellConfig.ts` (`team-config` section for TeamLead + Admin) · `utils/constants.ts` (`ORG_SETTINGS`; `ADMIN_BROKERAGE` removed) · `pages/TeamPage.tsx` (production KPIs + agents table + teams rail) · `components/dashboard/admin/IntegrationsCard.tsx` (→ `/organization?section=integrations`) · `types/api.ts` (`User.profile_settings_json` added — it was referenced but missing from the type).

**Two intentional deviations from the spec above:**
1. **Portal preferences are one combined "Preferences" pane**, not separate "Milestone Sharing / Agent BIO / Support" rail entries. The Client/FSBO settings card stacks were folded in verbatim under a single pane (one fetch, one save) for lower risk — all the same cards are present. Internal roles get the full multi-section rail.
2. **A4 placement:** the four team-config pages live in a dedicated **Team Config** sidebar group (visible to TeamLead + Admin), not appended to the Admin group. This honors "surface to Team Leads" while keeping the Admin group Admin-only governance.

**Design refinements (2026-05-29, post-review feedback):**
- The sidebar **footer "Settings" gear was removed** — the avatar menu's **Account** entry is the sole entry point (Organization stays in the avatar menu for internal roles).
- The **Account modal was restyled to match the New Transaction modal**: dark blurred overlay (`bg-[rgba(15,20,30,0.55)]` + blur), large rounded panel with a floating close button, and a branded `bg-ve-sidebar` left rail (champagne-glow accent, ✦ kicker, serif title, section nav) beside a white content pane. It no longer uses the Radix `<Dialog>` host (custom overlay + Escape/click-outside, mirroring `NewTransactionModal`).
- The **Profile avatar is now a direct upload** (click or drag-drop) — client-side center-crop + downscale to a ~256px JPEG data URL saved into `avatar_url` (a plain string column; no backend/storage change). The URL-paste field is gone. Object-storage-backed uploads still land with M6.1.
- The **Company field was removed from the Profile section** (it read oddly as a per-user field; organization name lives on the Organization page).

**Deferred (noted as a follow-up, not blocking):** the per-section unsaved-changes guard (§11). Each section still has an explicit Save bar; closing the modal does not currently prompt on a dirty Profile field (the standalone ProfileModal previously did). Worth adding a `useDirtyGuard` later.

---

## 1. Why this plan exists

Two threads converge here:

1. **Redundancy (verified 2026-05-29).** After M5.3 shipped, the Admin sidebar group, the Team group, and the Settings page presented several apparently-duplicated surfaces. Investigation found one true duplicate (Task Templates), one real soft overlap (Brokerage Overview vs Team Overview), one mislabeled-but-correct two-tier (personal vs team config), and a nav-access gap. See §4.
2. **Redesign feedback.** The Profile surface and the personal preference sections should be consolidated, and the personal-settings surface should be a **modal** rather than a page — while tenant/workspace configuration is split out to its own page.

This plan resolves both in a single, coherent information architecture.

---

## 2. The target information architecture

```
AVATAR MENU (every role)
  Account        → opens ACCOUNT MODAL (lands on Profile section)
  Organization   → navigates to /organization        (internal roles only)
  Log out

ACCOUNT MODAL   (overlay; in-app open, or via /settings?section=…)
  role-aware section rail + scrollable pane
  ─ Profile (identity)              ← folds in today's ProfileModal
  ─ Notifications
  ─ My Closing Checklist Templates  ← "My" prefix restored
  ─ My Tagged Notes
  ─ My Preferred Vendors
  ─ My Internal Resources
  ─ Help & tour
  (Client variant adds: Milestone Sharing Defaults · Agent BIO [read-only])
  (FSBO   variant adds: Milestone Sharing Defaults · Support Contact · Boundary Notice)

ORGANIZATION PAGE   /organization   (internal roles; per-section edit-gated)
  ─ Company           (admin / owner editable; read-only otherwise)
  ─ Branding          (admin)
  ─ AI configuration
  ─ Email integrations / E-signature
  ─ Danger Zone       (owner / platform-admin)

TEAM GROUP (sidebar, TeamLead + Admin)        ADMIN GROUP (sidebar)
  Team Overview   ← gains pipeline columns      Team Checklist Templates
  Team Members                                  Team Tagged Notes
  Task Templates  ← SOLE home                    Team Vendors
  Vendor Templates                               Team Internal Resources
                                                 Communication Audit · AI Governance ·
                                                 Payment Access · Audit Log
                                                 (Brokerage Overview REMOVED)
```

**The rule going forward:** identity/personal → Account modal; tenant config → Organization page; team playbook → Team/Admin groups. Every future preference lands in exactly one of these.

---

## 3. Section ownership (where everything ends up)

| Today | Current location | → New home |
| --- | --- | --- |
| Identity (avatar, name, email RO, phone, company, bio) | `components/profile/ProfileModal.tsx` | **Account modal → Profile** |
| Notifications | `SettingsPage.tsx` §`notifications` | **Account modal** |
| Checklist templates (personal) | `SettingsPage.tsx` §`my-checklist-templates` | **Account modal → My Closing Checklist Templates** |
| Tagged notes (personal) | §`my-tagged-notes` | **Account modal → My Tagged Notes** |
| Preferred vendors (personal) | §`my-preferred-vendors` | **Account modal → My Preferred Vendors** |
| Internal resources (personal) | §`my-internal-resources` | **Account modal → My Internal Resources** |
| Help & tour | §`help` | **Account modal → Help & tour** |
| Company | §`company` | **Organization page** |
| Branding | §`branding` | **Organization page** |
| AI configuration | §`ai` | **Organization page** |
| Email integrations / E-signature | §`integrations` / §`esign` | **Organization page** |
| Task templates (hardcoded mock) | §`templates` (`SettingsPage.tsx:668-713`) | **DELETED** — canonical home stays `/admin/task-templates` (Team group) |
| Danger Zone | §`danger` | **Organization page** |
| Client settings (Notifications · Milestone Sharing · Agent BIO) | `pages/client/ClientSettingsPage.tsx` | **Account modal (Client variant)** |
| FSBO settings (Notifications · Milestone Sharing · Support · Boundary) | `pages/fsbo/FsboSettingsPage.tsx` | **Account modal (FSBO variant)** |

---

## 4. Redundancy inventory (verification findings)

| # | Item | Verdict | Evidence | Resolution |
| --- | --- | --- | --- | --- |
| A | **Task Templates** appears as a Settings section **and** in the Team group | **True duplication** — the Settings section is a hardcoded, non-functional stub (5 fake rows, unwired Edit/Import); the real CRUD is `/admin/task-templates` | `SettingsPage.tsx:668-713`; `FRONTEND_UI_WORKFLOW_LOGIC.md §6.3` line 657 + line 2252 ("Visual-only… Real template management lives at /admin/task-templates"); `NAVIGATION_TEAM_ADMIN_REORG_PLAN.md §3.2 (problem 6), §8.4` | **Delete the stub entirely** (no link-out). Single home = `/admin/task-templates`, already linked from Team Overview quick-links (`TeamPage.tsx:578-592`). |
| B | **Brokerage Overview** vs **Team Overview** | **Real soft overlap** — both are read-only agent/team roster snapshots, same `/admin/users/:id` drill-down, both shown to an Admin; they differ only in metric emphasis (people/seats vs production/pipeline) | `pages/TeamPage.tsx` vs `pages/admin/AdminBrokerageOverviewPage.tsx`; M5.3 plan never references the pre-existing `/team` page | **Merge** the production lens into Team Overview; delete the Brokerage page. |
| C | **Team config pages** (Admin) vs **"My" sections** (Settings) | **NOT a functional duplicate** — personal writes `users.profile_settings_json`, team writes `teams.settings_json`; same editor *components* reused by design; team values inherited server-side | backend `app/api/v1/admin_team.py` (writes `teams.settings_json`); M5.3 plan §3.2 line 209 ("same editor, different storage target"), §12 acceptance lines 1035-1042; `M53Editors.tsx` | **Labeling fix only:** restore the spec-mandated **"My"** prefix (dropped in `SettingsPage.tsx:96-99`). The Account-modal/Admin split makes personal-vs-team unmistakable. |
| D | Team-config nav access | **Inconsistency** — routes are guarded `requiredRole="TeamLead"` but the Admin sidebar group renders for Admin only, so a Team Lead has no nav link to the team-config pages they own | `App.tsx:691-707` (TeamLead guards) vs `dashboardShellConfig.ts:90-96, 113` (Admin-only group) | Surface the four `/admin/team-*` pages to Team Leads. |

---

## 5. Workstream A — Redundancy elimination

These are largely subsumed by the redesign; A3/A4 are independent and ship first.

- **A1 — Task Templates.** Delete the §`templates` block in `SettingsPage.tsx:668-713`. Do **not** add a replacement link. Rationale: Task Templates is a *Team playbook* surface per the IA rule (`NAVIGATION_TEAM_ADMIN_REORG_PLAN.md §5`), not tenant config; a third pointer would re-create the echo this cleanup removes; §8.4 explicitly allows "remove the tab."
- **A2 — "My" labels.** The four personal sections render as **My Closing Checklist Templates / My Tagged Notes / My Preferred Vendors / My Internal Resources** inside the Account modal; team versions keep **Team …** in Admin.
- **A3 — Merge Brokerage Overview → Team Overview.** Add Pipeline + Active-Tx to the Team Overview KPI strip, add those columns to the roster, and add a per-team production rail — sourced from the existing `GET /api/v1/admin/brokerage/overview`. Then delete `AdminBrokerageOverviewPage.tsx`, the `/admin/brokerage` route (`App.tsx:682-687`), `ROUTES.ADMIN_BROKERAGE`, and the Admin sidebar entry (`AppLayout.tsx:364`). **Keep** the backend endpoint (now feeds Team Overview).
- **A4 — Nav access.** Surface the four `/admin/team-*` pages to Team Leads (e.g., show them to TeamLead in the relevant group, or add a TL-visible sub-group), matching M5.3 §0.4/§6.F intent. *(One small product confirmation when we reach it: keep them TL-visible vs. tighten the routes to Admin-only.)*

---

## 6. Workstream B — The Account modal

**6.1 Context** — `src/contexts/AccountModalContext.tsx` (replaces `ProfileModalContext.tsx`):

```ts
type AccountSectionId =
  | 'profile' | 'notifications'
  | 'my-checklist-templates' | 'my-tagged-notes'
  | 'my-preferred-vendors' | 'my-internal-resources'
  | 'help'
  // portal-only:
  | 'milestone-sharing' | 'agent-bio' | 'support-contact'

interface AccountModalValue {
  isOpen: boolean
  section: AccountSectionId
  open: (section?: AccountSectionId) => void
  close: () => void
  setSection: (s: AccountSectionId) => void
}
```

Mounted once at app root, replacing the `ProfileModalProvider` + `<ProfileModal/>` mount at `App.tsx:259-270`.

**6.2 Component** — `src/components/account/AccountModal.tsx` (replaces `ProfileModal.tsx`):
- Hosted in the shared Radix `<Dialog>` (`components/ui/dialog.tsx`) but **large**: desktop ≈ `min(960px, 92vw) × min(680px, 88vh)`; **full-screen on mobile**. Internal layout mirrors the current Settings page — sticky left section rail + scrollable right pane (reuse the rail/pane structure and editorial primitives from `SettingsPage.tsx`).
- **Role-aware section set**: internal roles get the seven personal sections; Client/FSBO get Profile + their portal cards; Vendor gets Profile (+ Notifications if applicable).
- The **Profile** section is the current `ProfileModal` body verbatim — saves `PATCH /api/v1/users/me` with the `profile_settings.agent_bio` mirror (unchanged).
- All other sections reuse the **existing** editors/hooks (`M53Editors.tsx`, `useM53Settings.ts`); Client/FSBO sections call the existing `/api/v1/client/settings` and `/api/v1/fsbo/settings`.

**6.3 Extraction** — move the personal section components currently inside `SettingsPage.tsx` (`NotificationsSection`, `ChecklistTemplatesSection`, `TaggedNotesSection`, `PreferredVendorsSection`, `InternalResourcesSection`, the Help pane) and the shared primitives (`SectionHead`, `RowList`, `SaveBar`, `EditorBody`, `SettingRow`) into `src/components/account/sections/` so the modal renders them. Save-per-section behavior is preserved.

---

## 7. Workstream C — The Organization page

- Repurpose `SettingsPage.tsx` → `src/pages/organization/OrganizationPage.tsx`. Keep **Company · Branding · AI configuration · Email integrations · E-signature · Danger Zone**; remove the personal sections (now in the modal) and the Task Templates stub (A1).
- Deliberately keeps OAuth redirects (Gmail/Outlook), the DocuSign **wizard modal**, and the destructive Danger Zone `useConfirm` flow on a **page**, not inside the Account modal — avoiding nested-modal / redirect-in-dialog hazards.
- **Visible to all internal roles** (agents need the email/e-sign connections), with the **existing in-section gating** preserved (`canEditTenant` for tenant fields; owner / platform-admin for Danger Zone).
- Re-point the admin dashboard `IntegrationsCard.tsx:32` link from `ROUTES.SETTINGS` → `ROUTES.ORG_SETTINGS`.

---

## 8. Routing & entry points (D2 — keep routes, open modal)

- **New** `src/pages/settings/OpenAccountModalRoute.tsx`: element for `/settings`, `/client/settings`, `/fsbo/settings` that, on mount, reads `?section=` → `open(section)` and renders `<Navigate to={landingRoute} replace />`, so a bookmark opens the modal over the user's dashboard. In-app opens (avatar menu, footer gear) call `open()` directly — no navigation.
- **`ROUTES`** (`utils/constants.ts`): add `ORG_SETTINGS = '/organization'`; keep `SETTINGS` / `CLIENT_SETTINGS` / `FSBO_SETTINGS` (now modal-openers); remove `ADMIN_BROKERAGE`.
- **Avatar menu** (both copies — `AppLayout.tsx:773-786` and `:1065-1078`): "Account" → `accountModal.open('profile')`; "Organization" → `navigate(ORG_SETTINGS)` (internal only). **Footer gear** (`:710-730`) → `accountModal.open()`. The role-based `settingsRoute` (`:462-467`) is no longer needed for navigation.
- **Print Checklist preview** is unaffected: the modal's checklist section still dispatches `ve:open-checklist-preview` (today at `SettingsPage.tsx:1200`); `PrintChecklistModal` stacks on top (Radix supports stacked dialogs).

---

## 9. Files — new / changed / deleted

| Action | File | Note |
| --- | --- | --- |
| **New** | `contexts/AccountModalContext.tsx` | `open(section?)`, section state |
| **New** | `components/account/AccountModal.tsx` | large Dialog, role-aware rail + pane |
| **New** | `components/account/sections/*` | extracted personal sections + Profile + portal cards |
| **New** | `pages/organization/OrganizationPage.tsx` | from SettingsPage minus personal/Task-Templates |
| **New** | `pages/settings/OpenAccountModalRoute.tsx` | route → opens modal |
| **Changed** | `App.tsx` | provider/modal mount, route table, Org route, brokerage route removed |
| **Changed** | `layouts/AppLayout.tsx` | avatar menu, footer gear, Admin group (drop Brokerage; TL access) |
| **Changed** | `utils/constants.ts` | add `ORG_SETTINGS`; remove `ADMIN_BROKERAGE` |
| **Changed** | `components/dashboard/admin/IntegrationsCard.tsx` | link → `ORG_SETTINGS` |
| **Changed** | `pages/TeamPage.tsx` | merge in pipeline/active-tx + teams rail |
| **Changed** | `layouts/dashboardShellConfig.ts` | TL nav access for team-config |
| **Deleted** | `components/profile/ProfileModal.tsx` | absorbed into AccountModal/Profile section |
| **Deleted** | `contexts/ProfileModalContext.tsx` | replaced by AccountModalContext |
| **Deleted** | `pages/settings/SettingsPage.tsx` | → OrganizationPage |
| **Deleted** | `pages/client/ClientSettingsPage.tsx` | folded into Account modal (Client) |
| **Deleted** | `pages/fsbo/FsboSettingsPage.tsx` | folded into Account modal (FSBO) |
| **Deleted** | `pages/admin/AdminBrokerageOverviewPage.tsx` | merged into Team Overview |

---

## 10. Backend impact

**None required.** Every surface calls endpoints that already exist: `/users/me`, `/notifications/preferences`, `/me/checklist-templates|tagged-notes|preferred-vendors|internal-resources`, `/client/settings`, `/fsbo/settings`, `/tenants/current`, integrations, and `/admin/brokerage/overview` (retained to feed Team Overview). This is a pure frontend re-composition.

---

## 11. Risks & mitigations

| Risk | Mitigation |
| --- | --- |
| Edit-heavy, 7-section surface inside a dialog feels cramped | Large desktop dialog; full-screen on mobile; per-section save bars (existing pattern); the split keeps OAuth/DocuSign/Danger Zone on the Organization page, out of the modal |
| Unsaved-changes loss when switching sections / closing | Per-section dirty tracking + guard (extends today's single `window.confirm` in ProfileModal) before section change or close |
| "Start tour" from the Help section conflicts with the modal overlay | `close()` the modal first, then start the tour |
| Bookmarked `/settings` has no "previous page" | Route opens modal over `landingRoute`; closing returns to landing — documented behavior |
| Mobile ergonomics | Modal renders full-screen on small viewports; rail collapses to the existing horizontal section nav |
| Stacked dialogs (checklist Preview over Account modal) | Radix Dialog supports stacking; verify focus-trap/escape ordering |

---

## 12. Phasing

1. **Phase 1 — Redundancy (independent).** A3 (Brokerage → Team Overview merge) + A4 (TL nav access). No dependency on the modal; lowest risk.
2. **Phase 2 — Split.** Carve `OrganizationPage` out of `SettingsPage`; extract personal sections into `components/account/sections/`; delete the Task Templates stub (A1). App still works as pages.
3. **Phase 3 — Modal.** Build `AccountModal` + `AccountModalContext`; fold in Profile + Client/FSBO sections; wire `/settings*` routes to open it; delete `ProfileModal`, `ClientSettingsPage`, `FsboSettingsPage`.
4. **Phase 4 — Wiring & docs.** Avatar menu / footer gear / Organization sidebar entry; "My" labels (A2); documentation sync (§13).

---

## 13. Documentation sync (part of the work)

- `MILESTONE_5_3_IMPLEMENTATION_PLAN.md` §0.2 (three-surface model), §3.2, §6.B (Profile-as-modal), §6.D/§6.E (Client/FSBO settings pages): record that Profile + personal Settings + portal settings are now one **Account modal**, and tenant config is the **Organization page**.
- `FRONTEND_UI_WORKFLOW_LOGIC.md` §6.3 (Settings as-built), §10 (Admin section — remove Brokerage Overview), §11.1 (Profile).
- `NAVIGATION_TEAM_ADMIN_REORG_PLAN.md` §8.4: mark the Task Templates dual-home **resolved** (stub deleted).

---

## 14. Acceptance criteria (click-paths a non-developer can run)

- Any role → avatar → **Account** → modal opens on Profile → edit bio → Save → toast; switch to **My Preferred Vendors** → reorder → Save; **Help & tour** → Start tour → modal closes, tour runs.
- Client → avatar → **Account** → sections are Profile · Notifications · Milestone Sharing · Agent BIO (read-only); **no** Organization entry.
- FSBO → avatar → **Account** → Profile · Notifications · Milestone Sharing · Support Contact · Boundary Notice.
- Internal → avatar → **Organization** → `/organization`; Admin can edit Company; an Agent sees it read-only; there is **no** Task Templates section anywhere on this page.
- Bookmark `/settings?section=notifications` → dashboard renders with the Account modal open at Notifications.
- Admin sidebar shows **one** agent/team overview (Team Overview, now with Pipeline + Active-Tx); **no** separate Brokerage Overview.
- A **Team Lead** can reach Team Checklist Templates / Tagged Notes / Vendors / Internal Resources from the sidebar.
- Task Templates is reachable from exactly **one** place — the Team group `/admin/task-templates` (plus its existing Team Overview quick-link).

---

## 15. Non-goals

- No backend, database, or RLS changes.
- No white-label branding UI (still M6.1), no new AI infrastructure.
- No change to Active Transactions, the wizard, portal shells, or per-deal surfaces.
- No change to the *team* config pages' behavior beyond surfacing them to Team Leads (A4).
- Avatar upload remains URL-paste until M6.1 (unchanged).
