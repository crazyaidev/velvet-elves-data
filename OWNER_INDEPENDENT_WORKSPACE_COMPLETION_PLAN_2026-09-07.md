# Owner-independent workspace completion plan

**Date:** 2026-09-07  
**Status:** Plan only. No product source is changed by this document.  
**Repos:** `velvet-elves-frontend`, `velvet-elves-backend`  
**Evidence:** `AGENT_WORKSPACE_INDEPENDENCE_REVIEW_2026-09-07.md` (viewport re-check + additional findings 4–8)  
**Identity contract:** `ROLE_IDENTITY_INDEPENDENT_WORKSPACE_PLAN_2026-09-03.md`  
**Signup roles in scope:** Agent, Transaction Coordinator (`TransactionCoordinator`), Team Lead (`TeamLead`), Admin

This plan **executes** the remaining identity work. It does not replace the 2026-09-03 contract. Where the review found the shipped chrome still failing a founder at 1366×768, this document is the source of truth for the fix.

---

## 0. Decision

> A newly created tenant owner must be able to run a complete workspace on day one **in the identity they signed up as**. Ownership is a billing/org badge on that same person. It must never replace the chosen role, never force them through another role’s console, and never depend on a tall monitor or a buried Settings heading named Organization.

“Independent workspace” here means all of:

1. **Identity home** — landing, brand, primary CTA, and empty states for that role.
2. **Identity setup** — mailbox, e-sign, automation-for-my-files, fees, and (Agent) representation, reachable from that home without opening Admin Console.
3. **Owner job** — company, branding, prepaid-deal billing, invites, change-my-role — **on screen at laptop size**, in every founder identity including Admin.
4. **Honest chrome** — no dead CTAs, no Settings tiles that bounce, no tour copy that promises another role’s tools.
5. **Invitee mode** — the same identity without the Owner job.

A role is a product identity, not a permission filter. Admin is a job. Owner is a legal/billing fact. Do **not** auto-promote anyone to Admin to make this true.

---

## 1. Definition of done (all four founder roles)

A tester creates a **new** password account (and a matching OAuth account) for each of Agent, Transaction Coordinator, Team Lead, and Admin. Viewport **1366×768** is the bar; 1920×1080 is extra, not the design target.

Without scrolling the sidebar, without already knowing a URL, and without becoming a different role, that founder can:

| # | Day-one job | Agent | TC | Team Lead | Admin |
|---|---|---|---|---|---|
| A | Land on **their** home, branded as that identity | `/dashboard/agent` · Transaction OS | `/dashboard/coordinator` · File Desk | `/dashboard/team` · Team Command, with a team row they lead | `/dashboard/admin` · Admin Console |
| B | See **+ New Transaction** (or + Open file) and use it | yes | yes | yes | yes (secondary “work a file” is fine; CTA still exists) |
| C | Open **Billing** and buy a prepaid deal | Owner chrome | Owner chrome | Owner chrome | Owner chrome |
| D | Open **Change my role** and switch among the four with the warned confirm | Owner chrome | Owner chrome | Owner chrome | Owner chrome |
| E | **Invite** staff (unlimited membership) | Owner chrome | Owner chrome | Owner chrome | Owner chrome |
| F | Connect **mailbox / e-sign** from identity setup | My setup | My setup | My setup | My setup or Admin home — not Integrations |
| G | Set **Trusted / You confirm** for *this workspace’s files* while they are the only staff user | My automation | My automation | My automation / team | Admin AI Governance (tenant floors) plus My automation if they still work files |
| H | Set **fee defaults** that follow the account (not only this browser) | My fees | My fees | My fees | optional; wizard still works |
| I | Set **representation default** (Buyer / Seller / both) | required | skip as identity (still pick a side on a file) | skip | skip |
| J | Complete the happy path **without** opening `/dashboard/admin` (unless they **are** Admin), AI Governance, Advertising, or Audit | yes | yes | yes | N/A — those **are** their job |
| K | Never see a primary **fake product** CTA (AI Coach Add / AI Coach Pro with no purchase) | yes | yes | yes | yes |

Invited (non-owner) staff of the same role get A, B, F, G, H, I, J, K and **must not** get C, D, E.

If any cell fails at 1366×768, the owner workspace is not independent yet.

---

## 2. Issue → work item traceability

From `AGENT_WORKSPACE_INDEPENDENCE_REVIEW_2026-09-07.md`. Every row is in scope. “All founders” means the same defect class on TC / Team Lead / Admin owners, not Agent-only chrome.

| Review | Defect (as observed) | Resolution in this plan |
|---|---|---|
| §1 | No prepaid-deal buy UI on the Agent home or any **visible** nav. Billing is a Settings tile / direct URL. Payments ≠ billing. | **P1** Owner strip always on screen includes **Billing**. Avatar menu **Billing** for owners. Optional home **prepaid-deals chip**. Copy stays “prepaid deals,” never “credits.” |
| §2 | Owner in data; **Change my role** / Users & Invites off-screen at 1366×768; not in avatar menu. “Settings → Organization” is not a nav path. | **P1** Pin Owner strip. Avatar: Change my role, Settings. Settings hub group label **Owner**, not a fake Organization menu. |
| §3 | Dashboard **AI Real Estate Coach** banner; Add / See how it works have no `onClick`. Not a product. | **P1** Hide `CoachAddOnBanner` (Agent and TC, because TC mounts the same page). Same for Team Lead coach banner live Add. |
| §4 | No **My setup**. Identity config only after opening Settings. No representation default. Fees are `localStorage`. Onboarding is not identity-shaped. | **P2** My setup sidebar group. **P3** persist representation + fees. **P4** onboarding tracks. |
| §5 | Settings **Workspace** tiles (Task / Vendor templates, Team Playbook) shown to Agent **owner** via `teamLeadOrOwner`; `RoleRoute` bounces to the Agent home. APIs still 200 via `require_role` owner bypass. | **P2** cards match identity, not owner. **P5** stop owner bypass on Team Lead **library** APIs. |
| §6 | My automation `PUT` writes **tenant** posture (owner bypass). After a second staff user that is identity collapse. Needs You `library_send_off` → `/admin/confidence` (403 / one pass logged out). | **P3** solo-alias only while sole internal staff; then Agent/TC cannot write tenant. Recovery links use `automationSettingsPath`. Never session-kill on Admin URLs. |
| §7 | Owner strip missing Billing, Branding, Danger. Intelligence also below the sidebar fold at 1366×768. | **P1** complete Owner strip in the **pinned** footer stack (not inside the scrolling nav). Work nav (incl. Intelligence) stays scrollable. |
| §8 | Empty queue: “prospect or chase referrals.” Tour promises integrations / team setup to every internal role. Analytics **AI Coach Pro** lock cards in source. | **P4** identity empty states + tours. **P1** hide Coach Pro gates until a real add-on exists. |

---

## 3. Already shipped — do not redo

Keep these. This plan closes the **holes**, not the identity model.

| Shipped | Where |
|---|---|
| Signup honors Agent / TC / Team Lead / Admin | `auth_service.py`, `oauth_service.py`, `accountTypes.ts` |
| Default omitted role → Admin (missed dropdown) | `DEFAULT_SELF_SIGNUP_ROLE`, `DEFAULT_ACCOUNT_ROLE` — **do not revert** to Agent |
| Team Lead signup mints a team and attaches the founder | starter kit |
| TC landing `/dashboard/coordinator` (File Desk brand) | `getLandingRoute`, `CoordinatorDashboardPage` |
| Exact-role dashboards; Agent owner cannot open Admin Console | `RoleRoute` `ownerBypass: false` on identity homes |
| `permissions.ts`: `isAdminIdentity` ≠ `canManageWorkspace` | frontend |
| Change-my-role page + owner four-way switch + TL mint / leadless | `SettingsChangeRolePage`, `PUT /users/{id}/role` |
| Transfer ownership does not force-promote to Admin | tenants API |
| Scope snap after second internal staff | `ve_identity_scope_snap_v1` default **true** |
| `require_admin_identity` vs `require_workspace_admin` on ads, audit, AI floors | backend |
| Settings Personal tiles: Connections, Playbook, My automation, My fees | exist; they are **not** in Agent chrome |
| Billing page `/organization?section=billing` + wallet `can_manage_billing` for owners | exists; **not visible** on the workspace |
| Users & Invites at `/admin/users` with Invite for this Agent owner | exists; **not visible** at laptop size |
| Invited Agent has no owner Settings tiles | `settingsCards.test.ts` |

Stale identity-plan comments (OAuth always Admin, TC shares Agent home, Team Lead has no team) are **historical**. Do not implement those as if they were still open.

---

## 4. Target chrome contract (viewport-proof)

The 1366×768 failure is structural: Owner links live in the **scrollable** `<nav>`, while **+ New Transaction** and the avatar are **pinned**. Intelligence and Owner therefore sit below Workflow, above the pin, and never paint.

### 4.1 Split the sidebar into two regions

`AppLayout.tsx` today: one `overflow-y-auto` nav, then pinned CTA + avatar.

**Target:**

```
┌─────────────────────────────────────┐
│ KPIs (compact)                      │  not scrolled off by Owner
├─────────────────────────────────────┤
│ SCROLLABLE work nav                 │
│  Dashboard                          │
│  Deals / Workflow / Payments /      │
│  Vendors / Intelligence             │
│  Team (Team Lead, Admin)            │
│  Oversight (Admin identity only)    │
├─────────────────────────────────────┤
│ PINNED (always in the 768px viewport)│
│  My setup          ← identity       │
│  Owner             ← owners only    │
│  + New Transaction / + Open file    │
│  Avatar (role + OWNER badge)        │
└─────────────────────────────────────┘
```

Pinned Owner + My setup must remain usable at **1366×768**. If the pin is too tall, Owner items become a compact icon row (Billing, Invites, Role, Company) with a “Owner” overflow menu — still on screen, still not inside the scrolling work nav.

Do **not** “fix” this by asking the user to scroll the sidebar.

### 4.2 Owner strip contents (founders of every role)

When `is_tenant_owner` (and not an invited member):

| Item | Route | Today | Target |
|---|---|---|---|
| Billing | `/organization?section=billing` | Settings tile only (after wallet probe) | **Pinned Owner** + avatar menu |
| Users & Invites | `/admin/users` | Sidebar Owner (off-screen) + Settings | Pinned Owner |
| Change my role | `/settings/change-role` | Sidebar Owner (off-screen) + Settings | Pinned Owner + avatar menu |
| Company | `/organization?section=company` | Sidebar Owner (off-screen) | Pinned Owner or Settings Owner group — at least one **on-screen** path; prefer pin |
| Branding | `/organization?section=branding` | Settings only | Settings Owner group; optional pin |
| Delete organization | `/organization?section=danger` | Settings only | Settings Owner group only (danger stays off the home chrome) |

Admin founders **also** get this pin. Their Oversight group (Communication Audit, Audit Log) stays in the scrollable work nav — that is Admin identity, not Owner.

Invited staff: **no** Owner pin, no Billing, no Change my role.

### 4.3 Avatar menu

Internal roles, **always:** Settings, Help Center, Log Out.

Owners **additionally:** Billing, Change my role (above Settings).

Do not add Organization as a menu item. There is no Organization page-as-menu.

### 4.4 My setup (identity)

New sidebar section key `setup` (or reuse `settings` which currently returns `null` in `buildSection`). Visible to Agent, TC, Team Lead, Admin.

Items (exact set per identity in §6):

- My setup hub **or** direct links: Email & E-signature, My automation, My fee defaults, My Playbook, Email Templates, Representation (Agent only).

Prefer a **hub** at `/settings/my-setup` that renders the same card registry filtered to `group === 'personal'` identity cards (not Help & Tour, not Security). Detail pages stay as they are. This avoids a third information architecture.

Admin: My setup is “how I work files” (Connections, fees if they close deals). Tenant policy stays in Settings Workspace / Admin Console.

### 4.5 Customer words

- Prepaid **deals**, not credits.
- Owner, not Admin, for company/billing/invites.
- Organization is an **in-page Settings heading** only until renamed to **Owner** (§5). Never document “Settings → Organization” as navigation.

---

## 5. Settings hub honesty

Files: `settingsCards.ts`, `SettingsHubPage.tsx`.

### 5.1 Rename the owner group

`group: 'owner'` already exists. The hub labels it **Organization**. Change the visible label to **Owner**. Description: “Company, billing, and invites. This is ownership, not Admin Console.”

There is still no `/settings/organization` route. Company/Billing stay `/organization?section=…`.

### 5.2 Cards follow identity, not “owner ≈ Team Lead”

Today:

```ts
const teamLeadOrOwner = (u) => hasMinimumRole(u.role, 'TeamLead') || !!u.is_tenant_owner
```

That is the §5 bounce. Replace:

| Card | Visible to |
|---|---|
| Task Templates, Vendor Templates, Team Playbook | `isTeamLeadIdentity` **or** `isAdminIdentity` — **not** Agent/TC owner |
| Users & Invites | `canManageWorkspace` (owner or Admin) — keep; this is Owner work |
| Company, Branding, Billing | `canManageWorkspace` (Billing still `&& billingEnabled`) |
| Change my role, Delete Organization | `is_tenant_owner` (plus platform admin on delete) |
| AI Governance, Integrations, Advertising, Payment Access, Document Templates | `isAdminIdentity` only |

A card’s `visible()` must match the destination `RoleRoute` / `ProtectedRoute`. Add a unit test: **Agent owner sees zero tiles whose `to` is a Team Lead–only route.** Click-through of Task Templates must not be the test — the card must not render.

### 5.3 Wallet probe

Billing tile appears only when `useCreditWallet` succeeds. The review account’s wallet is 200; the tile exists in the DOM after the probe. Keep the probe. Pinned Owner **Billing** should render as soon as `is_tenant_owner` is true and show a loading/empty state if the probe is in flight, so owners do not wait on Settings to discover pay.

If billing is platform-disabled (404), hide Billing everywhere (pin, avatar, hub).

---

## 6. Identity setup per founder

### 6.1 Agent — “I originate and run my files”

**My setup:** Connections, Representation, My automation, My fee defaults, My Playbook, Email Templates, writing style (keep on Profile; link from My setup).

**Representation default (new):**

- Persist on the user (suggested: `users.representation_default` enum `Buyer | Seller | BuyerAndSeller | null`).
- Settings page `/settings/representation` (or a section on My setup).
- New Transaction wizard prefills `representation_choice` from this value; user can still change per deal.
- Onboarding Agent track includes the control (skippable → wizard asks).

**Must not:** Task template admin, Team Playbook admin, AI Governance, Advertising, Audit.

### 6.2 Transaction Coordinator — “I run the file”

Same My setup **minus** representation-as-identity.

`CoordinatorDashboardPage` still mounts `SoloAgentDashboardPage identity="coordinator"`. That reuses Agent widgets (acceptable for this plan) but **inherits the Coach banner**. Hide the banner for both identities until a real coach exists. Empty states already have coordinator copy in places — finish empty-queue / onboarding so they never say “prospect.”

Primary CTA stays **+ Open file**.

### 6.3 Team Lead — “I run a team’s files”

Landing already Team Command with a minted team. My setup: Connections, My automation (team posture — see §8), fees, Playbook. **Team Playbook / Task / Vendor templates** belong in Settings Workspace **and** may stay linked from Team Command (plan 3B) — that is this identity, not a borrowed Admin Console.

Owner pin still has Billing / Invites / Change role. Creating a **second** team can wait; do not send them to Admin Teams to exist.

### 6.4 Admin — “I run the brokerage OS”

Landing Admin Console. Owner pin still required (they are usually the founder). Workspace Settings cards (AI Governance, etc.) stay Admin-only.

They can work a file **without** switching to Agent. Do not send them through `/dashboard/agent`.

### 6.5 Invitees

Same identity My setup. No Owner pin. Cannot self-switch role. Cannot open Billing checkout (`can_manage_billing` false; 402 paywall “notify owner”).

---

## 7. Prepaid deals (purchase path)

The buy UI exists. The workspace does not present it.

**P1 (chrome):**

1. Owner pin → Billing.
2. Avatar → Billing (owners).
3. Optional Agent/TC/TL home chip: “Prepaid deals: N · Buy” → same billing section. Hide when `exempt` or billing 404.
4. Keep wizard 402 paywall as the in-flow recovery, not the only discovery path.
5. Invited staff: existing “Notify your admin/owner” copy. Prefer “workspace owner.”

**Do not** add a second wallet. **Do not** say “credits” in customer UI.

Platform test card copy on the billing pane may stay in test mode.

---

## 8. Automation: solo alias vs post-hire

### 8.1 Today

- `GET /automation/settings` — any internal role.
- `PUT /automation/settings` — `require_role(TeamLead, Admin)` **with global owner bypass**, so an Agent owner writes **tenant** `default_posture`.
- Kill switches on that PUT already require Admin identity.
- Scope snap does **not** cover this write.

That is correct **only** while `count_internal_staff == 1` (plan Phase 2B alias).

### 8.2 Target (complete, without a full per-user conductor rewrite)

Implement `require_my_automation_write` (name flexible):

| Caller | Sole internal staff | Second+ internal staff |
|---|---|---|
| Agent or TC, owner or invitee | PUT tenant default allowed (alias “this workspace is me”) | **403** with detail: switch identity to Admin, or invite an Admin. UI: My automation becomes **read-only** + that explanation. Per-deal override on a file still works. |
| Team Lead | PUT allowed (tenant default until a true team-layer exists; copy says “your team’s default”) | PUT allowed for team/tenant default as today for TL |
| Admin | PUT + kill switches | unchanged |
| Owner who is still Agent after hiring | cannot silently keep tenant write | must use Change my role or hire Admin |

Tests: Agent founder PUT 200; insert second Agent in tenant; same founder PUT 403; Admin PUT 200.

**True per-user posture** (deal → user → tenant) remains a follow-up. This plan still **fully** stops the independence leak after hire.

### 8.3 Needs You and recovery links

- Scheduler / “open automation” already uses `automationSettingsPath` in one banner — keep that.
- `needs_you_composer.py` `_RECOVERY["library_send_off"]` today → `/admin/confidence`. Change to identity-aware path (pass role, or a generic `/settings/my-automation` for non-Admin and `/admin/confidence` for Admin).
- **Never** send a non-Admin owner at an Admin identity URL. One Chrome pass to `/admin/confidence` ended on `/login`; treat that as a defect: Admin identity routes must `Navigate` to **landing**, not clear the session. Add a regression: Agent owner `GET /admin/confidence` stays authenticated on `/dashboard/agent`.

---

## 9. Backend guard leftover (`require_role` owner bypass)

`require_role` still returns immediately when `is_tenant_owner`. That is correct for **workspace-admin** (users list, tenant patch, billing). It is wrong for **Team Lead libraries** and mixed hierarchy.

**P5 inventory (close the §5 API leak):**

| Endpoint class | Guard target |
|---|---|
| Tenant patch, billing, invites, list users for invites, danger | `require_workspace_admin` (already / keep owner) |
| Ads, audit, confidence floors, document template **admin**, payment-access policy | `require_admin_identity` (already) |
| Task templates write, vendor templates, team playbook admin, `GET /teams` if it is TL/Admin roster management | **Team Lead or Admin identity** — Agent/TC **owner must 403** |
| `PUT /automation/settings` | §8.2, not raw owner bypass |

Frontend `useTeams(!!owner)` on Change my role: if `GET /teams` becomes TL/Admin-only, the switcher must use a **workspace-admin** teams list (new query or `require_workspace_admin` on GET) so an Agent owner can still attach/create a team **when switching to Team Lead**. Do not force them to open Team Lead pages before the switch.

---

## 10. Fake products and first-run copy

### 10.1 Hide until real

| Surface | File | Action |
|---|---|---|
| Agent/TC home coach banner | `SoloAgentDashboardPage.tsx` `CoachAddOnBanner` | Do not render. Optional “Coming soon” without Add / See how it works buttons is acceptable; **no** dead primary CTA. |
| Team Lead coach banner / modal Add | `TeamLeaderDashboardPage.tsx` | Same: no live Add. Locked teaser in Intelligence for **teamed** users may stay **Locked** if it opens an honest coming-soon modal (Team Lead page already has that pattern). |
| Analytics AI Coach Pro cards | `AnalyticsPage.tsx` `ProGateCard` | Do not render until there is checkout. |
| `AI_COACH_ENABLED` | `AISuggestionsPage.tsx` | Stay false. |

### 10.2 Empty states

`identityCopy.ts` + `SoloAgentDashboardPage` empty action queue:

- Agent: “Open your first transaction — drop a contract or use + New Transaction.”
- TC: existing file-desk empty copy; no “prospect.”
- Team Lead / Admin: keep coverage / invite-or-open-file copy.

Transactions list already has `transactionsEmptyCopy`. Align the dashboard empty queue with it.

### 10.3 Tour

`tourSteps.tsx` `internalSteps` is shared. Split or skip by role:

- Agent/TC: Settings copy = profile, connections, **your** automation and fees. **No** integrations, **no** team setup, **no** Admin dashboard.
- Team Lead: team + Settings Workspace libraries.
- Admin: Oversight + Workspace policy.
- Skip steps whose `data-tour` target is missing (already auto-skipped) **and** do not mention those features in the account-menu step.

### 10.4 Onboarding tracks

`OnboardingWizard.tsx` `buildSteps` / complete CTAs:

| Track | Extra / different |
|---|---|
| Agent | Representation; finish CTA “Create your first transaction” (already close); copy “from your desk,” not “later from Active Transactions” as the only story |
| TC | File-desk copy; skip representation identity; “Open your first file” |
| Team Lead | Confirm team name; optional invite (already a complete-step card) |
| Admin | Company; “Go to Admin Console”; work-a-file secondary |

Posture step: owners only, as today. Stale comments (“founder→Admin”, “role is not pickable”) must match `canEditRole` / default Admin.

---

## 11. Persistence for identity config (P3)

### 11.1 Representation

- Column or JSON on `users` (migration).
- `GET/PATCH /users/me` (or a small `/users/me/identity-setup`) includes `representation_default`.
- Wizard reads it once on new intake.

### 11.2 Fee defaults

Today: `ve-wizard-last-fees` in `localStorage`; Settings My fees reads/writes that.

Target: same JSON shape stored on the user. Settings My fees load/save server. Wizard `loadLastFees` prefers server, falls back to localStorage once, then migrates up.

Do **not** build a brokerage fee catalog in this plan (Admin optional later).

### 11.3 Writing style

Already on Profile (`WritingStyleCard`). Link from My setup. Do not duplicate onto Admin Governance for Agent owners.

---

## 12. Phased delivery

Each phase leaves all four roles able to log in. Prefer **frontend P1+P2** first (the user’s visible failure), then backend P3/P5.

### P0 — Spec freeze (this document)

- This file is the completion contract.
- No product code.

### P1 — Visible owner workspace (frontend)

**Unblocks review §1, §2, §3, §7 (chrome), §8 (fake coach).**

- Sidebar pin: My setup + Owner (complete Billing / Invites / Change role / Company as in §4.2).
- Avatar: Billing + Change my role for owners.
- Hide Coach banners and Analytics Coach Pro.
- Home prepaid-deals chip (owners, billing enabled).
- Tests: `AppLayout` owner pin present for Agent owner; absent for invited Agent; Billing in pin; Coach banner not in `SoloAgentDashboardPage` output.

**Exit:** 1366×768 screenshot of each founder home shows Owner Billing and Change my role without scrolling the work nav. No Coach Add button.

### P2 — Settings honesty + My setup (frontend)

**Unblocks §4 (discoverability), §5 (dead tiles).**

- Hub label Owner; `teamLeadOrOwner` removed from Agent/TC.
- `/settings/my-setup` (or sidebar links) to identity cards.
- settingsCards tests: Agent owner cannot see Task Templates; Team Lead can; invited Agent has no Owner group.

**Exit:** Agent owner Settings has no bounce-tiles. My setup is on screen in the pin.

### P3 — Identity config that survives the browser (frontend + backend)

**Unblocks §4 (missing surfaces), §6 (posture after hire), §8 (Needs You link).**

- Representation default + fee defaults on the user.
- Automation PUT rule §8.2 + tests.
- Recovery links identity-aware; Admin URL does not log the Agent out.

**Exit:** New Agent founder sets representation and fees, logs in elsewhere, wizard prefills. After inviting a second Agent, founder cannot PUT tenant posture without switching identity.

### P4 — First session copy (frontend)

**Unblocks §8 remainder + onboarding.**

- Empty states, tour splits, onboarding tracks.

**Exit:** Four onboarding finishes look like four jobs. Agent empty queue does not say “prospect.”

### P5 — Guard leftover (backend + switcher)

**Unblocks §5 API leak.**

- Team Lead library endpoints no longer owner-bypass.
- Change-my-role still lists/creates teams via workspace-admin.

**Exit:** Agent owner `GET /task-templates` 403 (or read-only inherit globals without admin UI). Switching to Team Lead still mints/attaches a team.

### P6 — Hardening

- Register × 4 roles: landing, pin, billing 200 checkout session create (test mode), change-role round trip, invited Agent has no pin.
- Chrome QA: one headless Chrome, 1366×768, existing Vite+API, no extra servers.
- Update review doc status to “resolved” only after P1–P5 exit.

---

## 13. Primary files (implementation map)

### Frontend

| Area | Files |
|---|---|
| Sidebar pin / Owner / My setup | `src/layouts/AppLayout.tsx`, `src/layouts/dashboardShellConfig.ts` |
| Avatar | `src/layouts/AppLayout.tsx` |
| Settings registry / hub | `src/pages/settings/settingsCards.ts`, `SettingsHubPage.tsx`, new `SettingsMySetupPage.tsx` optional |
| Coach / empty | `src/pages/dashboards/SoloAgentDashboardPage.tsx`, `TeamLeaderDashboardPage.tsx`, `src/utils/identityCopy.ts` |
| Analytics lock | `src/pages/AnalyticsPage.tsx` |
| Fees / representation | `SettingsMyFeesPage.tsx`, wizard `wizardTypes.ts` / `NewTransactionWizard.tsx`, new settings page |
| Change role (already) | `SettingsChangeRolePage.tsx` |
| Onboarding / tour | `OnboardingWizard.tsx`, `tourSteps.tsx` |
| Needs You link | `NeedsYouPage.tsx` (already uses `automationSettingsPath`) |
| Tests | `settingsCards.test.ts`, `permissions.test.ts`, AppLayout/shell tests, Register/onboarding tests |

### Backend

| Area | Files |
|---|---|
| Automation write rule | `app/api/v1/automation.py`, `app/core/auth.py` or small helper, `test_automation_posture.py` / new identity tests |
| Recovery URLs | `app/services/needs_you_composer.py` |
| User identity fields | `users` schema, `users.py` me/patch, wizard consumers |
| Team Lead libraries | `task_templates.py`, team playbook / vendor template routers, `teams.py` GET split if needed |
| Tests | `test_identity_workspaces.py` extensions |

### Data (docs only)

- This plan.
- After ship: mark the 2026-09-07 review resolved; do not silently rewrite history — add a “Resolved” section.

---

## 14. Verification (tester script)

Use **new** accounts. Do not promote anyone to Admin to pass.

For **each** of Agent, TC, Team Lead, Admin:

1. Register with that role (password). Confirm landing URL + brand §1 table.
2. At **1366×768**, without scrolling the work nav: Billing, Change my role, My setup (or Admin policy home), + New Transaction / Open file.
3. Avatar: Billing + Change my role only if owner.
4. Open Billing; confirm prepaid-deal checkout starts (test mode). Do not need to complete Stripe for code review; confirm session URL.
5. Connect mailbox (or skip) from My setup — 200, not 403.
6. Agent only: set representation; start wizard; choice is prefilled.
7. Set My automation; save 200.
8. Invite a second Agent. Original Agent: deal list snaps to assignment; My automation save **403** with switch/invite copy; Billing still works; still not Admin Console.
9. Switch identity to Admin via Change my role (warned); land on Admin Console; ownership unchanged. Switch back.
10. Confirm no Coach **Add** button on home. Confirm Settings has no Task Templates tile for Agent/TC.

Invitee Agent in that tenant: no Owner pin, no Billing checkout, no Change my role.

OAuth: one Agent founder via Google/Microsoft state role — same pin, not forced Admin.

---

## 15. What we will not do

- Will not auto-promote the founder to Admin, on signup, on 403, on a Settings card, or on ownership transfer.
- Will not treat `is_tenant_owner` as Admin identity on dashboards or Admin-only APIs.
- Will not give invited staff the Owner pin or tenant checkout.
- Will not reintroduce seat / member caps. Membership stays unlimited; billing stays per deal.
- Will not ship a fake AI Coach purchase.
- Will not document **Settings → Organization** as a path.
- Will not rely on 1920×1080 or “scroll the sidebar past Workflow.”
- Will not clone the full task-template library per tenant at mint.
- Will not revert default signup role from Admin to Agent (that was an explicit product choice for missed clicks). Independence is “whatever they **picked**,” including Agent.
- Will not split into four apps.
- Will not implement true per-user automation precedence in this plan (deal → user → tenant). Post-hire Agent/TC lose **tenant** write instead (§8.2).

---

## 16. Suggested implementation order (when coding is approved)

1. **P1** chrome pin + hide fake Coach — this is what the founder actually cannot see.
2. **P2** Settings cards + My setup — stop bounce-tiles and bury-identity.
3. **P3** representation, server fees, automation hire-guard, recovery links.
4. **P4** onboarding / empty / tour.
5. **P5** Team Lead library API guards + switcher teams list.
6. **P6** four-role Chrome QA at 1366×768.

Frontend-first is allowed: P1+P2 do not wait on migrations. P3/P5 need backend.

---

## 17. Success

A person who creates an **Agent** account is an Agent: they see Agent home, Agent setup, and Owner billing/invites/role-switch **on a laptop**, without becoming Admin and without a dead Coach CTA.

The same sentence holds with the nouns swapped for **Transaction Coordinator**, **Team Lead**, and **Admin**.

That is a completely independent owner workspace at account creation, regardless of the role created.
