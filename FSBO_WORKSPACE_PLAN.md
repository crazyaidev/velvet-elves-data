# FSBO Workspace — Rebuild Plan (rev 4)

*Drafted: 2026-05-21. Review-corrected (rev 3 → rev 4): 2026-05-21.*

Rev 4 reviews rev 3 against the **current state of the repo** and corrects
several stale claims. Rev 3 was written against an older snapshot and
proposes work that has since shipped. The good direction in rev 3 is kept
(naming, page-tree discipline, tool-vs-dashboard split, `FsboPropertyTile`
naming); the stale work items are dropped, and a much smaller residual scope
is reframed honestly.

---

## 0. Review corrections in rev 4 (vs rev 3)

Each item below is grounded in a current file/line reference.

1. **The property-detail, documents, and milestones backend endpoints
   already exist.**
   - `GET /api/v1/dashboard/fsbo/properties/{transaction_id}` —
     [dashboard_role.py:393](velvet-elves-backend/app/api/v1/dashboard_role.py#L393)
   - `GET /api/v1/dashboard/fsbo/documents` —
     [dashboard_role.py:474](velvet-elves-backend/app/api/v1/dashboard_role.py#L474)
   - `GET /api/v1/dashboard/fsbo/milestones` —
     [dashboard_role.py:526](velvet-elves-backend/app/api/v1/dashboard_role.py#L526)
   Rev 3's "add these endpoints" item is dropped; the remaining work is
   verifying their response shapes against the workflow doc and tightening
   PII/visibility filtering as needed.

2. **Share-link authorization is already enforced.** Rev 3 framed this as a
   security gap, but [share_link_service.py:66, 98–115, 139](velvet-elves-backend/app/services/share_link_service.py)
   already calls `fsbo_workspace.assert_fsbo_transaction_access` on create
   and revoke, and `list_links` branches on `UserRole.FOR_SALE_BY_OWNER` to
   constrain to `list_fsbo_owned_transaction_ids`. The comment on line 65
   even cites "plan §6.7, §7.1." Rev 4 keeps **tests** to verify this stays
   enforced, but removes the "tighten authorization" task.

3. **`FsboDocumentsPage` is no longer the hardcoded-zero placeholder rev 3
   describes.** The current file's docstring
   ([FsboDocumentsPage.tsx:4-5](velvet-elves-frontend/src/pages/fsbo/FsboDocumentsPage.tsx#L4))
   states: *"Replaces the previous placeholder UI (every column hardcoded
   to 0) with the real backend projection."* It already consumes
   `useFsboDocuments()` and renders `group.board.columns` from real data.
   The remaining work is visual alignment + ensuring uploads carry
   `doc_type`.

4. **`FsboPropertyDetailPage` already reads its own endpoint.**
   [FsboPropertyDetailPage.tsx:29, 48](velvet-elves-frontend/src/pages/fsbo/FsboPropertyDetailPage.tsx) imports
   `useFsboProperty` and calls `useFsboProperty(id)`. It does NOT read
   `useFsboOverview()` as rev 3 claims.

5. **Overview data is not hardcoded.** In
   [dashboard_role.py:363, 378, 382-385](velvet-elves-backend/app/api/v1/dashboard_role.py#L363),
   `critical_next_steps` is computed (`next_steps`), `recent_milestones`
   comes from `fw.recent_milestones(tasks_by_tx)`, and `ai_guidance.next_decision`
   is computed (`next_decision`). The `glossary` is a static list of four
   terms — reasonable as a glossary, not "hardcoded guidance."

6. **`/fsbo/share` and `/fsbo/ask-ai` are not routes — by design.**
   - [App.tsx:108-117](velvet-elves-frontend/src/App.tsx) explicitly redirects
     `/sharing` for FSBO users back to `/fsbo`; share management is the
     **`FsboShareManagementModal`** mounted once at
     [App.tsx:215](velvet-elves-frontend/src/App.tsx#L215) inside
     `FsboShareProvider`, opened via `useFsboShare().open()` from any
     surface.
   - [dashboardShellConfig.ts:131-138](velvet-elves-frontend/src/layouts/dashboardShellConfig.ts#L131)
     states: *"Ask AI is the floating button only, Notifications live in the
     topbar bell, and Sharing is reachable via the footer Share CTA and
     Property Detail 'Manage' link."*
   - `FsboAskAiPage.tsx` and `FsboSharingPage.tsx` **no longer exist** on
     disk. The constants file does not export `FSBO_ASK_AI` or `FSBO_SHARE`.
   Rev 4 removes them from the page tree.

7. **Sidebar already has no Help group.** Current sidebar
   ([AppLayout.tsx:408-421](velvet-elves-frontend/src/layouts/AppLayout.tsx#L408)):
   *Workspace* group only, with **My Properties / Documents / Milestones &
   Messages**. Dashboard is rendered standalone at the top via
   `showStandaloneDashboardLink`. Rev 3's "keep Workspace and Help sections"
   recommendation is stale.

8. **`FsboPropertyTile` naming is correct.**
   [useDashboard.ts:693](velvet-elves-frontend/src/hooks/useDashboard.ts#L693)
   already exports `FsboPropertyCard` as a response type. A new visual
   component must use a different name — `FsboPropertyTile` is the right
   choice. Rev 4 keeps this.

9. **Endpoint namespace decision stays.** The dashboard namespace
   (`/api/v1/dashboard/fsbo/...`) is the one used by the four existing
   endpoints and by [useDashboard.ts:727, 830, 855, 882](velvet-elves-frontend/src/hooks/useDashboard.ts).
   Reconcile `FRONTEND_UI_WORKFLOW_LOGIC.md` to match (it still says
   `/api/v1/fsbo/...` in places).

10. **The real remaining defects are smaller than rev 3 implied.** They are
    visual/structural, not data/security:
    - `_shell.tsx` (`FsboPortalShell`) renders a tab bar
      ([_shell.tsx:11-16, 35-51](velvet-elves-frontend/src/pages/fsbo/_shell.tsx)).
    - `FsboOverviewPage` also renders a separate `PageTabBar`
      ([FsboOverviewPage.tsx:41-53, 144-150](velvet-elves-frontend/src/pages/fsbo/FsboOverviewPage.tsx)).
      These are two different implementations of the same four-tab affordance.
    - `_shell.tsx:28` uses `max-w-[1300px] mx-auto p-6` and
      `FsboOverviewPage:154` passes `maxWidth="1300px"`. Both diverge from
      the project's standard edge padding.
    - Overview still uses the older `DashboardPage` / `DashboardHeader` /
      `KpiStrip` / `RailCard` set; the project has been migrating to
      `DashboardCard` / `DashboardKpiCard` / `MainRailGrid`.
    - Property Detail's body, while wired to the real endpoint, is still
      thin (address + state + closing date + missing-doc count) and does not
      render the full milestone timeline / key dates / property documents /
      AI guidance / share links that the detail endpoint can supply.

11. **Total scope correction.** Rev 3 estimated ~7 dev days assuming
    significant backend work. Rev 4 estimates **~3.5 dev days plus QA** —
    the residual is mostly frontend cleanup, one Property Detail body
    expansion, and doc reconciliation.

---

## 1. Goals

The FSBO workspace should feel like a calm, external-facing portal for an
unrepresented seller. Show what to do next; which documents are missing or
under review; which milestones have changed; what can be safely shared.
Never leak internal workflow data.

This rebuild is **remediation**, not redesign:

- one intentional navigation system — keep the approved portal-tab
  affordance, but stop maintaining two implementations of it;
- a dashboard-like Overview and tool-like sub-pages;
- one Property Detail page that actually renders the rich payload the
  detail endpoint already returns;
- doc reconciliation so `FRONTEND_UI_WORKFLOW_LOGIC.md` matches the as-built
  routes/endpoints/decisions;
- no new LLM calls for rendering — reuse cached AI guidance or `FloatingAskAi`.

---

## 2. Authoritative sources

- `FRONTEND_UI_WORKFLOW_LOGIC.md` §8 (FSBO Customer Workspace).
- `SYSTEM_DESIGN.md` (FSBO role, route tree, dashboard API namespace).
- `STYLE_GUIDE.md` §15 (shell) and §16 (cards).
- `ROLE_DASHBOARDS_DESIGN_UPDATE_PLAN.md` rev 5 (FSBO Phase C visual
  direction; sidebar-footer CTA pattern).
- `MILESTONE_5_1_DASHBOARD_REMEDIATION_PLAN.md` (FSBO shell, portal tabs,
  upload, search/notification safety, role-matrix tests).
- `ATTORNEY_WORKSPACE_PLAN.md` and the [feedback memories](../../.claude/projects/c--Projects/memory/)
  (`feedback-design-benchmarks`, `feedback-attorney-workspace-rules`,
  `feedback-root-cause-over-patches`, `feedback-tool-vs-dashboard-aesthetic`) —
  the lessons this rebuild inherits.
- `completed_designs/ve-fsbo_dashboard.html` — preferred visual intent.
- Current frontend: `src/pages/fsbo/*`, `src/layouts/AppLayout.tsx`,
  `src/layouts/dashboardShellConfig.ts`, `src/hooks/useDashboard.ts`,
  `src/hooks/useDocuments.ts`, `src/components/documents/PortalDocumentList.tsx`,
  `src/components/dashboard/ShareMilestoneModal.tsx`,
  `src/contexts/FsboShareContext.tsx`,
  `src/components/fsbo/FsboShareManagementModal.tsx`.
- Current backend: `app/api/v1/dashboard_role.py`,
  `app/services/share_link_service.py`, `app/services/fsbo_workspace.py`,
  `app/api/v1/documents.py`, document/transaction schemas.

---

## 3. Current state (verified against the repo)

### 3.1 Already shipped — out of scope for this rebuild
- All four `/api/v1/dashboard/fsbo/...` endpoints (overview, properties/{id},
  documents, milestones) with response models in
  `app/schemas/dashboard_role.py`.
- Frontend hooks: `useFsboOverview`, `useFsboProperty(id)`, `useFsboDocuments`,
  `useFsboMilestones`.
- `FsboPropertyDetailPage` consumes `useFsboProperty`.
- `FsboDocumentsPage` consumes `useFsboDocuments` and renders the real
  Missing / In Progress / Uploaded / Verified / Complete board.
- `FsboMilestonesPage` consumes `useFsboMilestones`.
- Sidebar reduced to **Workspace** only (no Help group); Ask AI is
  `FloatingAskAi`; Notifications is the topbar bell; Sharing is the global
  `FsboShareManagementModal` opened via `useFsboShare().open()`.
- `share_link_service` enforces FSBO ownership on list/create/revoke; helpers
  in `app/services/fsbo_workspace.py` (`assert_fsbo_transaction_access`,
  `list_fsbo_owned_transaction_ids`).
- Document upload mutation supports `transactionId`, `docType`, `docLabel`
  ([useDocuments.ts:163](velvet-elves-frontend/src/hooks/useDocuments.ts#L163));
  `PortalDocumentList` wires `FlagForDeletionModal` + `useFlagForDeletion`.

### 3.2 Residual defects — in scope

1. **Duplicate portal-tab implementations.** Two separate four-tab bars
   exist: `_shell.tsx` tabs at lines 11-51, and `FsboOverviewPage`'s
   `PageTabBar` at lines 41-53 + 144-150. Same four destinations; two
   different components.
2. **Centered max-width gutters.** `_shell.tsx:28` uses
   `max-w-[1300px] mx-auto p-6`; `FsboOverviewPage:154` passes
   `maxWidth="1300px"`. Both diverge from the project's
   `px-3 md:px-5 xl:px-7 2xl:px-10` edge padding.
3. **Legacy dashboard chrome on Overview.** Uses `DashboardPage`,
   `DashboardHeader`, `KpiStrip`, `SectionCard`, `RailCard`. The project
   has been moving to `DashboardCard` / `DashboardKpiCard` / `MainRailGrid`
   (Solo Agent / Team Lead / Admin patterns). The Overview rebuild should
   follow.
4. **Property Detail body is thin.** The detail endpoint can supply the
   timeline / key dates / property documents / AI guidance / share links the
   §8.2 spec calls for; the page currently renders only a four-field summary
   and a one-line "Key dates" stub
   ([FsboPropertyDetailPage.tsx:26-52](velvet-elves-frontend/src/pages/fsbo/FsboPropertyDetailPage.tsx)).
   This is the largest residual UI gap.
5. **`FsboPortalShell` still owns its own header anatomy** (mono eyebrow
   `FSBO Workspace · {title}` + bespoke tab bar). It should be retired in
   favor of a standard FSBO page header that uses the project's
   `Group > [Page]` breadcrumb pattern and (optionally) renders a single
   `FsboPortalTabs` component reused by every portal-core page including the
   Overview.
6. **Workflow doc drift.** `FRONTEND_UI_WORKFLOW_LOGIC.md` §8 still
   references `/api/v1/fsbo/dashboard`, `/api/v1/fsbo/share-links`,
   `/api/v1/fsbo/notifications`, a "Sharing management page", and an
   "`/fsbo/ask-ai` full-page chat". None match the as-built. Reconcile.
7. **Document upload property/doc_type discipline.** Even though the upload
   mutation accepts `docType`, confirm the FSBO upload UI actually surfaces
   a property picker + doc-type picker (rev 3 §3.6); a silent default to
   `properties[0]` would still leave the board buckets imprecise.

### 3.3 Open question (not a defect — decide before Phase A)

**Portal tabs or sidebar-only?** The approved FSBO design and the dashboard
remediation plan still describe four portal tabs (Overview / Properties /
Documents / Support). Rev 3 wisely flagged that deleting all of them silently
is a product-design deviation. Rev 4 keeps that posture: **default to one
portal-tab implementation, four tabs**, but flag the choice explicitly in the
Phase A PR so product can sign off (or pivot to sidebar-only) in writing
before merge.

---

## 4. Functional inventory

| Capability | Status | Plan |
|---|---|---|
| Overview KPIs | Live | Migrate to shared dashboard kit (`DashboardKpiCard`) |
| "Your next step" critical-step card | Live (computed) | Keep; verify wording in `fsbo_workspace.next_steps_for` |
| Property portfolio strip (Overview) | Live | Extract `FsboPropertyTile`; share with `/fsbo/properties` |
| Property portfolio page | Live | Restyle as tool; reuse `FsboPropertyTile` |
| Property Detail | **Thin — biggest residual gap** | Render timeline / key dates / property docs / AI guidance / share links from the existing endpoint |
| Documents board | Live (real projection) | Visual polish only |
| Document upload | Mutation correct; UI may default | Ensure modal collects property + doc_type |
| Flag-for-deletion | Live (PortalDocumentList) | Preserve through any restyle |
| Milestones & Messages | Live (real projection) | Visual polish only |
| Sharing | Global modal via `FsboShareProvider` | No new surfaces; verify modal opens from every documented entry point |
| Ask AI | `FloatingAskAi` (by design) | Update workflow doc to bless the floating-widget MVP |
| Notifications | Topbar bell (by design) | Update workflow doc |
| Boundary notice | Live on Overview | Confirm presence on Property Detail and Documents |

---

## 5. Page tree (current + intended)

```text
/fsbo                         FSBO Overview dashboard            (live)
/fsbo/properties              Property portfolio                 (live)
/fsbo/properties/:id          Property Detail (expand body)      (live, thin)
/fsbo/documents               Documents board + upload modal     (live)
/fsbo/milestones              Milestones & Messages              (live)
/milestones/:token            Public read-only milestone viewer  (live, internal-style)
```

Not routes (intentional):
- Share management — `FsboShareManagementModal`, mounted globally in
  `FsboShareProvider`; opened via `useFsboShare().open()`.
- Ask AI — `FloatingAskAi` button.
- Notifications — topbar bell.

Decision register:
- **Portal tabs:** consolidate to one `FsboPortalTabs` component, four tabs
  (Overview / Properties / Documents / Support). Confirm with product in the
  Phase A PR description before merge.
- **API namespace:** `/api/v1/dashboard/fsbo/...` is the canonical namespace.
  No new `/api/v1/fsbo/...` endpoints.
- **Property visual component:** new component is named
  `FsboPropertyTile`. `FsboPropertyCard` is a backend response type and must
  not be a React component name.
- **Share CTA placement:** sidebar-footer (already in place); the CTA's
  click handler opens `useFsboShare().open()` (see
  [dashboardShellConfig.ts:131-142](velvet-elves-frontend/src/layouts/dashboardShellConfig.ts#L131)
  for the sidebar-footer pattern).
- **"Milestones & Messages" naming:** keep, because the backend projection
  includes messages
  ([dashboard_role.py:526](velvet-elves-backend/app/api/v1/dashboard_role.py#L526) and
  `_fsbo_visible_messages`).

---

## 6. Per-surface plan

### 6.1 Shell, tabs, margins, breadcrumb (Phase A — lands first)
- Build one `FsboPortalTabs` (in `src/components/fsbo/`) — keeps the four
  approved tabs.
- Delete `FsboOverviewPage`'s inline `PORTAL_TABS` / `TAB_TARGETS` /
  `PageTabBar`; consume `FsboPortalTabs` instead.
- Either retire `FsboPortalShell` or strip its bespoke tab bar and reuse
  `FsboPortalTabs`. Replace its `max-w-[1300px] mx-auto p-6` wrapper with
  the project's standard gutters.
- Switch the Overview's `DashboardPage maxWidth="1300px"` to the standard
  shell padding.
- Adopt the project's breadcrumb pattern (`Group > [Page]` with an icon)
  for FSBO sub-pages — e.g. `Home · My Properties > [Address]` on Property
  Detail.
- **Decision affordance for product:** if product wants sidebar-only navigation
  instead of portal tabs, remove `FsboPortalTabs` and the related workflow-doc
  language in the same PR. Do not silently flip the model.

### 6.2 Overview `/fsbo` (Phase B)
- Replace `DashboardPage` / `DashboardHeader` / `KpiStrip` / `SectionCard` /
  `RailCard` with `DashboardCard` / `DashboardKpiCard` / `MainRailGrid` to
  align with the Solo Agent / Team Lead / Admin pattern.
- Mount `FsboPortalTabs` once at the top of the content area (or in the new
  page header — pick one location consistent with where the portal-tab
  affordance lives across all FSBO pages).
- Use `FsboPropertyTile` in the portfolio strip; share status helpers with
  `/fsbo/properties`.
- Keep the **action banner**, **AI guidance card**, **coordinator rail
  card**, **recent milestones**, **concierge strip**, **boundary notice** —
  none need new data, only re-styling.
- No new LLM calls.

### 6.3 Property portfolio `/fsbo/properties` (Phase B)
- Drop `FsboPortalShell`'s centered gutters; use the new shell header.
- Reuse `FsboPropertyTile` (the one used by Overview).
- Keep the existing status filter; ensure the filter param drives a real
  filter against the backend, not a client-side hide.

### 6.4 Property Detail `/fsbo/properties/:id` (Phase C — main UI work)
- Page already calls `useFsboProperty(id)`; expand the body to render
  everything the endpoint returns:
  - Milestone timeline (with plain-English explanation) — already in the
    detail payload; align to the same tile pattern Attorney Matter Detail
    uses.
  - Key dates list.
  - Property documents (subset of `useFsboDocuments` for this property) —
    surface `PortalDocumentList` filtered to this transaction so
    flag-for-deletion stays available.
  - AI guidance card (cached from the endpoint).
  - Share links for the property + "Share milestones" CTA opening
    `useFsboShare().open()` pre-scoped to this property id.
  - Support contact + boundary notice.
- Use the "professional tool" `<section>` card vocabulary from the Attorney
  rebuild (quiet bordered sections, small icon + medium-weight title +
  divider), **not** `DashboardCard` chrome.
- No new endpoint required.

### 6.5 Documents `/fsbo/documents` (Phase D — light polish)
- Confirm the upload entry point is a **modal** (per §8 modal inventory)
  that collects property + `doc_type` + optional label and submits via
  `useUploadDocument({ transactionId, docType, docLabel })`. Do not let the
  UI silently default to `properties[0]`.
- Preserve `PortalDocumentList`'s flag-for-deletion wiring on any restyle.
- Visual alignment with the standard FSBO header + canonical gutters.

### 6.6 Milestones & Messages `/fsbo/milestones` (Phase D — light polish)
- Keep the page; restyle for the canonical FSBO header + gutters.
- Verify the `_fsbo_visible_messages` projection only surfaces external/
  coordinator-to-FSBO messages and never internal notes or audit-only
  chatter. Add a backend test if not present.

### 6.7 Share management (no new page)
- `FsboShareManagementModal` is the canonical surface. Verify it opens
  from:
  - Sidebar-footer "Share milestones" CTA
    ([dashboardShellConfig.ts:139](velvet-elves-frontend/src/layouts/dashboardShellConfig.ts#L139)).
  - Property Detail "Manage" / share-link CTA.
  - Property portfolio per-property "Share link" action (if surfaced).
- Each entry point should pre-fill the active property when known.

### 6.8 Workflow-doc reconciliation (Phase E)
- Update `FRONTEND_UI_WORKFLOW_LOGIC.md` §8 to match the as-built:
  - Endpoint namespace `/api/v1/dashboard/fsbo/...`.
  - Sharing = modal (`FsboShareManagementModal`), not `/fsbo/share` page.
  - Ask AI = `FloatingAskAi` button, not `/fsbo/ask-ai` page.
  - Notifications = topbar bell, not a separate page.
  - Sidebar = single Workspace group (Help group eliminated).
- Update any `SYSTEM_DESIGN.md` FSBO route stragglers.

---

## 7. Backend touchpoints

Smaller than rev 3 implied — most backend is done. The remaining items:

1. **Tests, not new code, on share-link authorization.** Add pytest cases
   for cross-owner list/create/revoke denial against
   `share_link_service` to lock the existing fix in place.
2. **`_fsbo_visible_messages` filter test.** Verify only external/
   coordinator-to-FSBO communication-log rows are returned; internal notes
   and audit-only rows are filtered out. If a portal-visibility column does
   not exist, derive visibility from `direction` + `channel` + recipient
   list.
3. **Property Detail payload audit.** Confirm
   `FsboPropertyDetailResponse` carries every field the §8.2 spec calls for
   (milestones, key dates, documents, ai_guidance, share links, support
   contact, boundary notice). Add only what's missing — do not rebuild the
   endpoint.
4. **Document `doc_type` discipline.** No backend change; the FSBO upload UI
   must pass `docType` so the documents board's Missing/In-Progress mapping
   stays accurate. Frontend-only.

No new endpoints. No new LLM calls. No schema changes.

---

## 8. Execution order (~3.5 dev days + QA)

### Phase A — Shell consolidation (~0.75 day)
- One `FsboPortalTabs` component. Delete the two duplicate tab
  implementations.
- Retire `FsboPortalShell`'s centered gutters; standardize edge padding on
  every FSBO page (including the Overview).
- Update the sub-page headers to the project's `Group > [Page]` breadcrumb
  pattern with the FSBO icon.
- PR description explicitly asks product to approve "keep portal tabs vs go
  sidebar-only" before merge.

**Exit criteria:** one tab component, no `max-w-[1300px]` wrappers,
breadcrumbs consistent.

### Phase B — Overview + Properties + `FsboPropertyTile` (~0.75 day)
- Migrate Overview to `DashboardCard` / `DashboardKpiCard` /
  `MainRailGrid`.
- Extract `FsboPropertyTile`; use it on Overview portfolio strip and the
  Properties list.
- Keep the action banner / AI guidance / recent milestones / concierge /
  boundary notice content.

**Exit criteria:** Overview matches the project's dashboard pattern;
Properties is a tool page; one shared tile.

### Phase C — Property Detail body (~1.25 days)
- Expand Property Detail to render the full `useFsboProperty(id)` payload:
  milestone timeline, key dates, property documents (via
  `PortalDocumentList` filtered to this id, preserving flag-for-deletion),
  AI guidance card, per-property share links with "Manage" → modal CTA,
  support contact, boundary notice.
- Use the "professional tool" section vocabulary, not `DashboardCard`.
- Add render tests and a pytest cross-owner 403/404 test on the existing
  detail endpoint.

**Exit criteria:** Property Detail renders every section the endpoint can
supply; flag-for-deletion still works inline.

### Phase D — Documents + Milestones polish (~0.5 day)
- Confirm/upgrade the Documents upload modal so it always collects property
  + `doc_type`.
- Restyle Documents and Milestones to the new canonical header + gutters.
- Add a backend test for `_fsbo_visible_messages` filtering.

### Phase E — Doc reconciliation + manual QA (~0.25 day)
- Update `FRONTEND_UI_WORKFLOW_LOGIC.md` §8 to match as-built (endpoints,
  sharing-as-modal, Ask-AI-as-floating, no Help group, namespaces).
- Manual QA against the checklist (§9). Capture screenshots in the PR.

**Total: ~3.5 dev days + QA.**

---

## 9. Verification checklist

Frontend:
- `npx tsc --noEmit -p tsconfig.app.json` — clean.
- `npx eslint <changed files>` — clean.
- Render tests:
  - exactly one `FsboPortalTabs` instance per FSBO page;
  - no `PageTabBar` import in `FsboOverviewPage`;
  - no `max-w-[1300px]` on any FSBO page;
  - Property Detail renders the full payload sections;
  - Documents upload modal requires both `transaction_id` and `doc_type`;
  - flag-for-deletion remains visible for unflagged documents.

Backend:
- `pytest app/tests -k "fsbo or share_link or documents"` — passes.
- Tests cover: FSBO overview scoped to current user; share-link
  list/create/revoke cross-owner denial; property-detail happy path + 403/404
  cross-owner; documents projection column mapping; `_fsbo_visible_messages`
  filtering; flag-for-deletion allowed for FSBO and blocked from hard delete.

Manual QA, logged in as an FSBO customer:
- Sidebar shows **Workspace** only — no Help group, no Ask-AI sidebar
  entry, no Notifications sidebar entry, no Sharing sidebar entry.
- Portal tabs (if kept) are exactly Overview / Properties / Documents /
  Support, rendered by a single component.
- No `max-w-[1300px]` centered gutters anywhere; pages use standard edge
  padding.
- Overview reads as a dashboard; Properties / Property Detail / Documents
  read as tools (quiet sections, not `DashboardCard` chrome).
- Property Detail loads from `useFsboProperty`, not `useFsboOverview`.
- Documents board counts match real Missing / In Progress / Uploaded /
  Verified / Complete totals.
- Upload modal tags property and doc_type.
- Share creation opens the same modal from sidebar CTA, property tile,
  and Property Detail; created links appear on the modal's list view.
- Cross-owner: a link created for one FSBO user's property cannot be
  listed or revoked by another FSBO user in the same tenant.
- Boundary notice visible on Overview, Property Detail, Documents.
- No string visible to the customer references internal milestones, phases,
  or version numbers; no internal task queue / AI briefing / communications
  panel leaks into the FSBO shell.

---

## 10. Risks and open decisions

1. **Portal tabs vs sidebar-only.** Rev 4 keeps the four-tab affordance by
   default and pushes the decision into the Phase A PR. If product asks for
   sidebar-only, remove `FsboPortalTabs` and update the workflow doc in the
   same PR — do not silently flip.
2. **Property Detail scope.** Phase C is the largest residual chunk. If it
   threatens to drift into reinvention, time-box it to the §8.2 sections
   only — don't add new capability under the rebuild banner.
3. **`_fsbo_visible_messages` truthfulness.** Confirm the filter precisely
   matches what's safe for an external user; if a portal-visibility column
   is missing, propose adding one rather than relying on `direction` /
   `channel` heuristics.
4. **Doc churn.** Updating `FRONTEND_UI_WORKFLOW_LOGIC.md` §8 may surface
   other stale FSBO claims (notifications, error states). Time-box doc
   reconciliation; don't let it block the merge of Phase A–D.

---

## 11. Cross-references

- `ATTORNEY_WORKSPACE_PLAN.md` — the source of the navigation, tool-page,
  and modal-vs-page lessons this plan inherits.
- `FRONTEND_UI_WORKFLOW_LOGIC.md` §8 — the FSBO user-journey spec to
  reconcile against the as-built (Phase E).
- `SYSTEM_DESIGN.md` — FSBO role, route tree, dashboard API namespace.
- `STYLE_GUIDE.md` §15–§16 — shell, gutters, cards.
- `ROLE_DASHBOARDS_DESIGN_UPDATE_PLAN.md` rev 5 — FSBO dashboard direction;
  sidebar-footer CTA pattern.
- `MILESTONE_5_1_DASHBOARD_REMEDIATION_PLAN.md` — FSBO shell, portal tabs,
  upload, search/notification safety, role-matrix tests.
- `completed_designs/ve-fsbo_dashboard.html` — visual benchmark.

---

*Plan drafted: 2026-05-21 (rev 1). Re-reviewed against current code:
2026-05-21 (rev 3 → rev 4).*
