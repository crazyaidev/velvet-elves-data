# Settings Design-System Standardization - Superior Plan

**Status:** Plan only. No source changes in producing this. Awaiting Jan sign-off.
**Date:** 2026-06-19
**Author:** Jan (drafted with Claude)
**Scope:** The visual design and layout of every page reachable from the Settings hub (`/settings`) - the hub itself, the six Personal detail pages, the nine Workspace pages, and the two Platform settings pages. This is a presentation-layer pass: I am standardizing shells, headers, section voices, cards, type, tokens, spacing, and save patterns. I am not changing any page's behavior, data, routes, or backend.
**Builds on:** `NAVIGATION_AND_SETTINGS_CONSOLIDATION_SUPERIOR_PLAN.md` (which created the hub and moved these pages under it). That plan unified *where* settings live; this plan unifies *how they look*.

---

## 0. Why this plan exists, and the bar I am holding it to

The consolidation put every setting in one place, but the pages behind the cards were built at different times by different patterns, so the hub now opens onto a grab-bag: a shadcn-card billing screen sitting next to an editorial hairline-row Organization page sitting next to a dashboard-card AI page. For a tool sold to real-estate professionals, that reads as unfinished. A professional tool feels like one surface: you should not be able to tell which screen was built first.

The bar:

- **One settings design language.** A user moving from Account to Branding to Users to Platform Billing should feel zero seams: same header, same section voice, same card, same type, same spacing, same save affordance.
- **Normative, not invented.** Everything here resolves to `STYLE_GUIDE.md` (the canonical token + composition source) and the v2 Comfort Scale. Where the Style Guide already names a pattern, I adopt it rather than inventing a new one. `/calendar` remains the in-app styling benchmark for header + pill + stat treatment.
- **Grounded in the real code.** Section 2 is a first-hand audit of every Settings page's current design state, with counts of the specific violations (non-`ve` colors, ad-hoc type sizes, competing components). The fixes in Section 6 reference those findings line-of-sight.
- **No regressions.** This is a re-skin. Controls keep their behavior, deep-links keep working, and the test suite stays green.

---

## 1. The diagnosis (what makes it feel miscellaneous)

Five concrete inconsistencies, each measured against the live source in Section 2:

1. **Four different page headers.** `SettingsDetailShell` header (Account/Notifications/Connections/Help), `AdminPageHeader` (AI Governance, Advertising, Integrations, Payment Access), `PlatformPageHeader` (Platform Advertising), and bespoke inline headers (Organization, Team Playbook, Users, Teams, Task Templates, Vendor Templates, Email Templates, Platform Billing). They differ in serif size (16/20 vs 18/22), kicker icon, and vertical padding (`pb-0` vs `pb-3`).
2. **Two competing section-head voices, neither v2-compliant.** `primitives.SectionHead` uses a `text-[9px]` mono kicker + `text-[22px]` serif. `AdminTeamSettingsPage` defines its *own* larger `SectionHead` (`text-[10.5px]` kicker, `text-[15px]` body). Both put a kicker below the v2 12px floor.
3. **Three card vocabularies.** Editorial hairline rows ("no boxes" - Organization, Account sections), the dashboard `SectionCard` (AI Governance, Advertising, Platform Advertising), and shadcn `Card`/`CardHeader`/`CardContent` (Platform Billing). Three different border radii, paddings, and header anatomies for the same job.
4. **Token and type violations.** `PlatformBillingPage` alone has 20 non-`ve` color classes (`text-gray-900`, `text-gray-500`, ...) plus `text-2xl`; `AdminPaymentAccessPage` has 1 non-`ve` color and uses `text-sm`. These break the "`ve-*` tokens only" and the px-based type-scale rules outright.
5. **Container-width and save-pattern drift.** Content widths range across `max-w-2xl`, `max-w-3xl`, `max-w-4xl`, `max-w-5xl`, and none. Saves are sometimes a `SaveBar`, sometimes inline buttons, sometimes auto-save with no signal - so the "how do I save this" answer changes per page.

---

## 2. Evidence base: current design state of every Settings page

Audited the live source (counts verified by grep on 2026-06-19).

| Page (hub card) | File | Header | Section voice | Card vocab | Layout | Width | Notable issues |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Settings hub | `SettingsHubPage` | inline serif "Settings" + search | n/a | hub card (new) | card grid | full | v2-ish already; reference target |
| Account | `SettingsDetailShell` + `ProfileSection` | DetailShell | primitives (9px kicker) | editorial rows | single col | `max-w-3xl` | kicker below v2 floor |
| Notifications | DetailShell + `NotificationsSection` | DetailShell | primitives | editorial | single col | `max-w-3xl` | same |
| Email & E-signature | DetailShell + `ConnectionsPanel` | DetailShell | primitives | editorial rows | single col | `max-w-3xl` | same |
| My Playbook | `SettingsMyPlaybookPage` | inline (own) | primitives | editorial | rail + pane | full | rail styling local |
| Help & Tour | DetailShell + `HelpSection` | DetailShell | primitives | editorial | single col | `max-w-3xl` | same |
| Email Templates | `EmailTemplatesPage` | inline | local | item card grid + Dialog | card grid | full | bespoke header + cards |
| Company / Branding / Billing / Danger | `OrganizationPage` | inline | primitives | editorial | rail + pane | `max-w-4xl` pane | local rail; primitives kicker |
| Users & Invites | `AdminUsersListPage` | inline | n/a | tables | list | full | bespoke header; table styles local |
| Teams | `AdminTeamsPage` | inline | n/a | team rows + Dialog | list | full | bespoke header |
| Task Templates | `TaskTemplateListPage` | inline | n/a | list + Dialog | list | full | bespoke header |
| Vendor Templates | `VendorTemplatesPage` | inline | n/a | item card grid + Dialog | card grid | full | bespoke header |
| Team Playbook | `AdminTeamSettingsPage` | inline | **local bigger SectionHead** | editorial | rail + pane | full | second section-head voice |
| Integrations & Webhooks | `AdminIntegrationsPage` | `AdminPageHeader` | n/a | **dashboard SectionCard** | cards | full | dashboard vocab on a settings page |
| AI & Automation | `AdminAIGovernancePage` | `AdminPageHeader` | n/a | **dashboard SectionCard** (x4) | cards | full | dashboard vocab |
| Payment Access | `AdminPaymentAccessPage` | `AdminPageHeader` | n/a | matrix | grid | `max-w-2xl` | `text-sm` + 1 non-`ve` color |
| Advertising | `AdminAdvertisingPage` | `AdminPageHeader` | n/a | **dashboard SectionCard** (x2) | cards | full | dashboard vocab |
| Platform Billing | `PlatformBillingPage` | bespoke inline | local | **shadcn Card** | cards | `max-w-5xl` | **20 non-`ve` colors**, `text-2xl`, worst offender |
| Platform Advertising | `PlatformAdvertisingPage` | `PlatformPageHeader` | n/a | **dashboard SectionCard** (x3) | cards | full | dashboard vocab; 4th header type |

Summary of violations to clear: 4 header components -> 1; 2 section-head voices -> 1 (v2); 3 card vocabularies -> 1 settings vocabulary; 21 non-`ve` color usages -> 0; ad-hoc `text-2xl`/`text-sm` -> the px scale; 5 container widths -> 1 rule.

---

## 3. The Settings Design System (the standard)

This is the single language every Settings page must speak. All classes resolve to existing `ve-*` tokens and the v2 Comfort Scale.

### 3.1 Three legitimate page archetypes (and nothing else)

Every Settings page is exactly one of these. Picking the archetype first prevents bespoke layouts.

- **A. Hub** - the card grid landing. One instance (`SettingsHubPage`); it is the reference, not a template to copy elsewhere.
- **B. Config page** - forms and toggles (Account, Notifications, Connections, Company, Branding, Billing, AI & Automation, Payment Access, Integrations, Platform Billing). Editorial voice: `SectionHead` + hairline `SettingRow`s, no boxes. Single reading column `max-w-3xl`, or, when a page has 3+ sub-sections, a 232px section rail + pane.
- **C. Collection page** - a set of records you create/edit (Users & Invites, Teams, Task Templates, Vendor Templates, Email Templates, Advertising, Platform Advertising). A header + optional toolbar (search / filter / one primary action) + a uniform `SettingsItemCard` grid or a uniform table + a `Dialog` editor.

### 3.2 The one shell (Archetype B and C)

Per Style Guide 15.1 and the "app pages own their scroll" rule:

```jsx
<div className="flex h-full min-h-0 flex-col overflow-hidden bg-ve-bg">
  <SettingsPageHeader … />                         {/* shrink-0, Section 3.3 */}
  <div className="min-h-0 flex-1 overflow-y-auto px-3 md:px-6 pt-6 pb-12">
    {/* Config: <div className="mx-auto max-w-3xl"> … </div>
        Rail+pane / Collection: full width */}
  </div>
</div>
```

Gutter is `px-3 md:px-6` everywhere. The width rule follows Style Guide 15.3: a **single-column reading form** centers at `max-w-3xl`, but any page or section with **side-by-side editors, a live preview, or a matrix drops the cap and fills the gutter**. Concretely that means Branding (editor + live preview, two columns) and Payment Access (role x capability matrix) keep a wider layout - they must NOT be forced to `max-w-3xl`. Collections and rail+pane pages fill the gutter. What this rule removes is *arbitrary* drift (the `max-w-5xl` on Platform Billing, the `max-w-2xl` on Payment Access used as a reading cap), not principled wide layouts.

### 3.3 The one header: `SettingsPageHeader`

Consolidate the headers into one component, carefully:

- **Keep `AdminPageHeader` as the implementation** (it already has the right anatomy and the `backTo`/`backLabel`/`backIcon` crumb-root override). It is also used by the Oversight **Audit Log** page, so it must keep working there - **alias** it as `SettingsPageHeader` rather than renaming it (a rename would break the Oversight + admin importers).
- Route the `SettingsDetailShell` header and every bespoke inline header (Organization, Team Playbook, Users, Teams, Task Templates, Vendor Templates, Email Templates, Platform Billing) through it.
- To also absorb `PlatformPageHeader`, add a **non-linked root mode** (a plain `Platform` label with no link, which is what `PlatformPageHeader` does today). `PlatformPageHeader` is shared by **Platform Advertising (settings) AND Platform Tenants (sidebar)**, so it cannot simply be retired: either migrate both platform pages (plus the sidebar AI usage page) to the unified header's plain-`Platform` root and then retire it, or leave the two sidebar platform pages on it. Either way, do not break Tenants / AI usage.

Anatomy (matches `/calendar` and Style Guide 15.2):
- Breadcrumb row: gear icon + `Settings` (links to `/settings`) + `›` + current page name. (Oversight pages that are not in Settings keep their own root.)
- Title: `font-serif text-[16px] md:text-[20px] text-ve-text-primary`.
- Optional inline badge chip next to the title (counts/status) - the `/calendar` pill style.
- Optional right-aligned primary action.
- Optional tab strip with the canonical `-mx-3 md:-mx-6` bleed.
- Container: `shrink-0 border-b-[1.5px] border-ve-border bg-white px-3 md:px-6 pt-3 pb-3`.

### 3.4 The one section voice: `SectionHead` (v2)

Standardize the editorial section voice on the v2 Comfort Scale and delete the divergent local copy in `AdminTeamSettingsPage`. Mind the blast radius: the shared `primitives.SectionHead` is imported (some via the relative `./primitives` path) by `ProfileSection`, `PersonalSections`, `PortalSections`, `OrganizationPage`, `ConnectionsPanel`, and `BillingPane`. Of those, only the **portal Account modal** (`ProfileSection` + `PortalSections`) is outside this plan's scope, so re-tuning the primitive also restyles the portal modal's section heads - an acceptable, consistent improvement. The **New Transaction wizard and the public Advertise landing page define their OWN local `SectionHead`** and are unaffected (verified). If we want zero portal ripple, add a `variant="settings"` prop that opts into the v2 sizes and pass it only from Settings consumers. Target sizes:

- Kicker: `font-mono text-[12px] tracking-[1.5px] uppercase text-ve-orange`, prefixed with `✦`. (Up from 9px; clears the v2 12px floor.)
- Title: `font-serif text-[20px] leading-[1.15] tracking-[-0.005em] text-ve-text-primary`.
- Description: `text-[13.5px] leading-relaxed text-ve-text-secondary`.
- Optional right-aligned `action` slot.

### 3.5 The one card: `SettingsItemCard` (Archetype C)

A single card shell for every collection item (webhook, template, ad creative, team):

- `rounded-xl border border-ve-border bg-white shadow-soft`, `p-5`, hover `shadow-card-hover` + `-translate-y-[1px]` only when the whole card is a link.
- Header: optional ~40px tinted icon tile -> serif `text-[16px]` title -> `text-[13.5px]` secondary line.
- One explicit primary action button per card (Style Guide 16.5 clickability rule); never make the whole card the target when it also has inline buttons.
- Grid: `grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4`.

This **replaces** the dashboard `SectionCard` on AI Governance, Advertising, and Platform Advertising, and the shadcn `Card` on Platform Billing. The dashboard `SectionCard` stays a dashboard component; Settings stops borrowing it so settings pages no longer read as mini-dashboards.

### 3.6 Forms, saves, and controls (Archetype B)

- Rows: `SettingRow` (label-left / control-right) inside `RowList` (hairline-divided, no boxes).
- Inputs/selects: the canonical `inputClass`; Radix `<Select>` only, never native `<select>` (Style Guide 9.3, anti-pattern 15).
- Toggles: one shared `ToggleRow` (the on/off switch currently re-implemented per page - extract it once).
- Save: one `SaveBar` (right-aligned, hairline-top footer - the current primitive, unchanged in behavior) showing a single brand-orange primary; auto-save sections show the `Auto-saves on edit` micro-label instead of a button, consistently. Making the bar sticky to the bottom of the pane is optional polish, not a requirement, and only if it works cleanly inside the `overflow-y-auto` container.
- Validation, empty states, skeletons: Style Guide 9.2 / 11 (explanatory empty states, a skeleton for every async section, no `window.confirm`).

### 3.7 Tokens, type, spacing, motion (global, non-negotiable)

- **Color:** `ve-*` tokens only. Zero `text-gray-*` / `text-slate-*` / raw hex. (Fixes the 21 violations.)
- **Type:** the v2 px scale - body 13.5px, labels 12.5px, kickers 12px, section titles serif 20px, nothing below 12px, no `text-2xl`/`text-sm`/`text-lg` ad-hoc sizes.
- **Spacing:** 4px grid; card padding `p-5`; section rhythm `space-y-6`/`space-y-8`.
- **Radii/shadows:** cards `rounded-xl`, modals `rounded-2xl`; `shadow-soft` rest, `shadow-card-hover` hover, `shadow-premium` for dialogs; never `shadow-2xl`.
- **Icons:** `lucide-react`, `h-4 w-4` list/row, `h-5 w-5` tile.
- **Motion:** 150ms ease-out hover, 250ms enter/exit, no bounce.

### 3.8 The rail (multi-section Config pages)

Organization, Team Playbook, and My Playbook share one `SettingsSectionRail`: 232px left rail, `border-l-[3px]` active accent in `ve-orange`, `text-[12.5px]` rows, with the mobile fallback being a horizontal pill strip. Extract the version already duplicated across those three pages into one component so they match exactly.

---

## 4. Shared components to create or consolidate

| Component | Action | Replaces |
| --- | --- | --- |
| `SettingsPageHeader` | **Alias** the existing `AdminPageHeader` (do not rename - it is also used by Oversight Audit Log); add a non-linked `Platform` root mode | the `SettingsDetailShell` header, the bespoke inline headers, and `PlatformPageHeader` (only after Tenants + AI usage migrate) |
| `SectionHead` (primitives) | Re-tune to v2 sizes (or add a `variant="settings"`); note this also restyles the portal Account modal | the local `SectionHead` in `AdminTeamSettingsPage` |
| `SettingsItemCard` | New, one collection-item card | dashboard `SectionCard` usage + shadcn `Card` on settings pages |
| `ToggleRow` | Extract the on/off switch once | per-page switch re-implementations |
| `SettingsSectionRail` | Extract the rail | duplicated rails in Organization / Team Playbook / My Playbook |
| `SettingsPageShell` (optional) | Thin wrapper = shell + header + scroll body | `SettingsDetailShell` (folded in) |

All live under `src/components/settings/`. None changes behavior; they are presentation wrappers around the existing controls.

---

## 5. Conformance pass: page-by-page

Each entry lists only the design deltas; functionality is untouched.

**Config pages (Archetype B)**
- **Account / Notifications / Email & E-signature / Help** - swap `SettingsDetailShell` for `SettingsPageShell` (same look, shared header); inherit the v2 `SectionHead` automatically.
- **Company / Branding / Billing / Danger (Organization)** - adopt `SettingsPageHeader` + `SettingsSectionRail`; already editorial, so only the kicker size and rail extraction change. **Keep the wider pane** (no `max-w-3xl` cap) for Branding's editor + live-preview two-column layout per Style Guide 15.3.
- **Team Playbook** - delete the local `SectionHead`, use the v2 primitives one; adopt `SettingsSectionRail`; header via `SettingsPageHeader`.
- **AI & Automation** - replace the 4 dashboard `SectionCard`s with the editorial voice (it is a config page, not a dashboard). Its two sub-components, `AiProviderSection` and `EmailAutomationSection` (in `components/dashboard/admin/`, used ONLY by this page - verified, not by any dashboard - and themselves rendering `SectionCard`), must be converted too, or no gate can claim the page is `SectionCard`-free. Keep every control's behavior.
- **Integrations & Webhooks** - webhook list becomes `SettingsItemCard`s; the register-endpoint form uses `SectionHead` + `SettingRow`.
- **Payment Access** - replace `text-sm` and the 1 non-`ve` color with the px scale + tokens; the role x capability matrix adopts `SectionHead` framing and drops its `max-w-2xl` cap to fill the gutter (a matrix is the side-by-side case in Style Guide 15.3), not `max-w-3xl`.
- **Platform Billing (largest job)** - remove shadcn `Card`/`CardHeader`/`CardContent`; rebuild as editorial `SectionHead` + `RowList` (Credit settings, Base prices) and `SettingsItemCard` (packs); replace all 20 `text-gray-*` with `ve-*`; drop `text-2xl` and `max-w-5xl`; route the header through `SettingsPageHeader` (Settings crumb is already added).

**Collection pages (Archetype C)**
- **Users & Invites / Teams / Task Templates** - headers via `SettingsPageHeader`; tables/rows adopt the shared row treatment; any list rows that are cards become `SettingsItemCard`.
- **Vendor Templates / Email Templates** - the template grids become `SettingsItemCard`; the `Dialog` editors adopt the canonical dialog (Style Guide 6.5); header via `SettingsPageHeader`.
- **Advertising / Platform Advertising** - replace dashboard `SectionCard`s with `SettingsItemCard` for ad/package/creative items; the approval queue keeps its actions; header via `SettingsPageHeader`.

**Hub**
- **Settings hub** - already on the target voice; only ensure its card shell and the new `SettingsItemCard` share one definition so the hub and the collection pages match.

---

## 6. Phasing (each phase ships green: `tsc` + `eslint` + tests)

- **Phase 1 - Foundations.** Re-tune `primitives.SectionHead` to v2; build `SettingsPageHeader` (promote `AdminPageHeader`), `SettingsItemCard`, `ToggleRow`, `SettingsSectionRail`, `SettingsPageShell`. No page wired yet; visual diff is zero.
- **Phase 2 - Config pages.** Convert Account, Notifications, Connections, Help, Organization, Team Playbook, AI & Automation, Integrations, Payment Access to the shared header + v2 section voice + rail. Delete the local `SectionHead`.
- **Phase 3 - Platform Billing rebuild.** The one structural rewrite: shadcn `Card` -> editorial voice, gray -> `ve-*`, width + type fixes.
- **Phase 4 - Collection pages.** Users, Teams, Task Templates, Vendor Templates, Email Templates, Advertising, Platform Advertising onto `SettingsPageHeader` + `SettingsItemCard` + canonical dialog. Migrate Platform Advertising off `PlatformPageHeader`; to actually retire `PlatformPageHeader`, also move the sidebar platform pages (Tenants, AI usage) onto the unified header's plain-`Platform` root - otherwise leave them on it and defer the retirement (their sidebar status is out of this plan's scope).
- **Phase 5 - Sweep + verify.** Grep-gate: zero non-`ve` colors and zero ad-hoc `text-2xl/-sm/-lg` across the Settings file set; one header import everywhere; run the screenshot gate (Section 7).

I work the phases in order without stopping; I do not commit (Jan commits).

---

## 7. Verification (the "squint test" for a non-developer)

- **Per-page screenshots, one strip.** Render each Settings page headless and lay the captures in a single column. A real-estate tester should be unable to tell which screen was built first: same header height, same kicker, same card radius, same button.
- **The squint test.** Blur the strip; the rhythm (header bar, section kicker, row hairlines, save bar) should repeat identically.
- **Automated gates.** `eslint` clean; a grep gate proving 0 `text-gray-*`/`text-slate-*`, 0 shadcn `from '@/components/ui/card'`, and 0 dashboard `SectionCard` usage across the **Settings file set** - defined as the hub + the Personal / Workspace / Platform-settings pages **and the components they render** (`ConnectionsPanel`, `BillingPane`, `AiProviderSection`, `EmailAutomationSection`). The gate intentionally does NOT cover `PlatformTenantsPage` or `InvoiceDetailModal`, which keep `SectionCard` legitimately as sidebar / non-settings surfaces. `tsc` clean; the test suite green (including `BillingPane.test.tsx`, which renders the page being re-skinned).
- **Click-path check.** Every page still saves, every dialog still opens, every deep-link still resolves (no behavior change).

---

## 8. Acceptance criteria

- [ ] One header component across all Settings pages (`SettingsPageHeader`); `PlatformPageHeader` retired for hub-hosted pages; no bespoke inline headers remain.
- [ ] One `SectionHead` voice (v2 sizes); the local `AdminTeamSettingsPage` copy is gone.
- [ ] One card vocabulary (`SettingsItemCard`); zero shadcn `Card` and zero dashboard `SectionCard` under the Settings file set.
- [ ] Zero non-`ve` color classes and zero ad-hoc `text-2xl/-sm/-lg` under the Settings file set (the 21 current violations cleared).
- [ ] Width per Style Guide 15.3: single-column forms `max-w-3xl`; multi-column / preview / matrix sections (Branding, Payment Access) fill the gutter; no arbitrary `max-w-5xl` / `max-w-2xl` reading caps.
- [ ] One save affordance (`SaveBar`) and one `ToggleRow`.
- [ ] Every page owns its scroll and uses the `px-3 md:px-6` gutter.
- [ ] Screenshot strip passes the squint test; `tsc`, `eslint`, tests green.

---

## 9. Risks and non-goals

- **Non-goals:** changing any control's behavior, the data it reads/writes, routes, role gates, or backend; redesigning the dashboards; altering the Oversight (sidebar) pages beyond their shared header.
- **Risk - Platform Billing rebuild touches working billing UI.** Mitigation: it is a re-skin of the same hooks/state; Phase 3 is isolated and screenshot-verified against the current behavior before and after.
- **Risk - converting dashboard `SectionCard` pages loses an intentional look.** Mitigation: AI Governance / Advertising are configuration, not dashboards; the editorial voice is the correct register and matches Organization. If product wants to keep a card look on a specific block, it uses `SettingsItemCard`, not the dashboard component.
- **Risk - churn across ~18 files.** Mitigation: Phase 1 lands the shared components with zero visual change, so later phases are mechanical swaps, each independently green and screenshot-checked.
- **Risk - the shared `SectionHead` ripples into the portal Account modal.** Acknowledged (Section 3.4): re-tuning it restyles `ProfileSection` / `PortalSections` in the portal modal. That is a consistent improvement; if undesired, the `variant="settings"` opt-in keeps the portal modal untouched. The wizard is verified unaffected (own local `SectionHead`).
- **Risk - `BillingPane` has a render test.** The Platform Billing rebuild and any `BillingPane` token fixes must keep `BillingPane.test.tsx` green; re-run it in Phase 3.
- **Out of scope (noted):** the sidebar platform pages (Tenants, AI usage) are work surfaces, not Settings, so this plan does not restyle them - even though `PlatformAIUsagePage` shares the same shadcn-`Card`/gray-token issues. A future sidebar-consistency pass can address them; flagged here so the inconsistency is a known decision, not an oversight.

---

## 10. Review log - flaws found in the first draft and corrected here

I re-read the live source to find workflow/logic errors before this plan is built against. Fixes folded in:

- **F1 - Shared `SectionHead` blast radius.** The draft framed "re-tune `primitives.SectionHead`" as Settings-only. It is imported (some via `./primitives`) by `ProfileSection`, `PersonalSections`, `PortalSections`, `OrganizationPage`, `ConnectionsPanel`, `BillingPane` - so it also restyles the **portal Account modal**. The wizard and public Advertise page use their own local `SectionHead` and are safe. Corrected Section 3.4 + added a `variant` escape hatch + a risk note.
- **F2 - `PlatformPageHeader` cannot be retired outright.** It is shared by **Platform Tenants (sidebar)** and Platform Advertising (settings), so "retire it" would break Tenants. Corrected Section 3.3 / 4 / Phase 4: add a non-linked `Platform` root to the unified header and migrate both, or defer retirement.
- **F3 - Don't rename `AdminPageHeader`.** It is also used by the Oversight **Audit Log**; a rename breaks importers. Corrected to **alias** it as `SettingsPageHeader`, keeping the original export.
- **F4 - The `max-w-3xl` width rule contradicted Style Guide 15.3.** Branding (editor + live preview) and Payment Access (matrix) need to fill the gutter, not be capped. Corrected Sections 3.2 / 5 / 8.
- **F5 - AI Governance conversion understated.** Its `AiProviderSection` + `EmailAutomationSection` sub-components (used only by that page, themselves rendering `SectionCard`) must be converted too for any "no `SectionCard`" gate to hold. Corrected Section 5.
- **F6 - `SaveBar` "sticky" was a new, unproven behavior.** Softened to the current right-aligned hairline-top footer; sticky is optional polish (Section 3.6).
- **F7 - Grep-gate scope.** Scoped explicitly to Settings pages + the components they render, and excluded `PlatformTenantsPage` / `InvoiceDetailModal`, which legitimately keep `SectionCard` (Section 7).

---

*End of plan. This document is plan-only; no source was changed in producing it.*
