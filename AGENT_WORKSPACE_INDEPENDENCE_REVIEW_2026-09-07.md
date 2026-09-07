# Agent workspace independence review

**Date:** 2026-09-07 · **Corrected:** 2026-09-07 (viewport re-check)  
**Status:** Findings only. No product source was changed.  
**Local account:** `taytum.calah@minafter.com` (Agent, owner)  
**App / API:** `http://127.0.0.1:5173` · `http://127.0.0.1:8000`

A role is a product identity. Ownership (`is_tenant_owner`) is a separate billing/org badge. This review does **not** recommend turning the Agent founder into Admin.

---

## Correction

The first version of this note was wrong to describe a path **Settings → Organization**.

That path **does not exist in the chrome**:

- There is **no** sidebar item named Settings or Organization.
- The avatar menu is only **Settings / Help Center / Log Out**. There is no Organization item.
- “Organization” is not a page or a menu. It is an **in-page heading** on `/settings`, under nine Personal cards. You only see it if you already opened Settings and scrolled (or have a tall monitor).

On a **1366×768** Agent home — the size this account was re-checked at — you see Dashboard, Deals, Workflow, **+ New Transaction**, and **Agent + OWNER** on the avatar. You do **not** see Organization, Billing, Change my role, or a Settings link.

What follows is what is actually on screen vs what only exists after extra clicks and scrolling.

---

## Verdict

The Agent workspace is not an independent workspace from the user’s point of view.

1. **No way to buy deals/credits from the Agent home or any visible nav.** The buy UI is a buried Settings card (and a direct URL), not something this workspace presents.
2. **This login is the tenant owner in data**, but **there is no visible role-update UI on the Agent home.** Change my role is off-screen in the sidebar and is not in the avatar menu.
3. **“AI Real Estate Coach” on the dashboard is a fake CTA**, not a product.

---

## Account (API — this part was already correct)

| Field | Value |
|---|---|
| Email | `taytum.calah@minafter.com` |
| `role` | `Agent` |
| `is_tenant_owner` | **true** (tenant `owner_user_id` matches) |
| `team_id` | `null` → lands on `/dashboard/agent` |
| Onboarding | completed |
| Wallet | HTTP 200, `can_manage_billing: true`, prepaid balance 1, fee $49 (test mode) |

Creating the account **did** set ownership. The product does not show that owner job on the Agent workspace the user is looking at.

---

## What you actually see (re-measured)

Checked in headless Chrome at **1366×768** (laptop) and **1920×1080** (tall desktop). Screenshots: `aime_automation_qa/artifacts_agent_workspace_review/vis_*`.

### Agent home (`/dashboard/agent`)

| | 1366×768 | 1920×1080 |
|---|---|---|
| Coach banner “Add the AI Real Estate Coach” | On screen | On screen |
| Avatar: Agent + OWNER | On screen | On screen |
| Sidebar: Settings | **Not present** | **Not present** |
| Sidebar: Organization | **Not present** | **Not present** |
| Sidebar: Billing / credits | **Not present** | **Not present** |
| Sidebar Owner group (Company, Users & Invites, Change my role) | **Off screen** (y ≈ 925–1045, viewport 768) | On screen near the bottom |
| Avatar menu | Settings, Help Center, Log Out | Same |

On the laptop layout this user is using, **Owner links never appear** unless they notice the sidebar itself can be scrolled past Workflow. The screenshot of the home page stops at Workflow + New Transaction + avatar. That matches “there is no UI to update roles.”

### How Settings is reached

Only: click the **avatar** (bottom of sidebar) → **Settings**. Not in the main nav, not in the header.

### Settings hub (`/settings`) — still not “Settings → Organization”

The hub is one long page. Groups are headings in the scroll, not a second menu.

At **1366×768**, without scrolling the Settings sheet:

- The page is **Personal** (nine tiles). That is the obvious content.
- The heading **Organization** sits at the **bottom edge** of the viewport (y ≈ 631 of 768). Easy to miss; it is not a destination you choose.
- **Change my role / Billing** tiles for that group sit **below** the laptop fold (Billing y ≈ 821). You must scroll the Settings body to use them.
- Avatar menu still has no Organization item.

At **1920×1080**, after opening Settings, the Organization **heading and tiles** (including Billing and Change my role) can fit on screen. That is a tall desktop, not the Agent home, and still not a nav path named Organization.

There is **no** `/settings/organization` route. Company/Billing live at `/organization?section=…`, which you only get by clicking a tile you have already found.

---

## 1. Purchase credits / prepaid deals

**On the Agent workspace the user sees: none.**

- Dashboard: no wallet, no “buy deals,” no “credits.”
- Sidebar: Payments is **Invoices & Payments**, not prepaid deals. No Billing link at 1366×768 (Owner group off screen; Billing is not in that group anyway).
- Avatar menu: no Billing.

**What exists only if you already know the URL or scroll Settings on a tall screen:**

- Tile **Billing** on the Settings hub (owner group, only after the wallet probe succeeds). Copy: “per-deal fee, prepaid deals,” never “credits.”
- Page `/organization?section=billing` — **Buy one deal** at $49. This account **can** pay (`can_manage_billing: true`).
- Wizard badge + 402 paywall after starting a deal.

The first note was inaccurate in calling this “Settings → Organization → Billing.” That is not how the UI is labeled or reached.

### Proposed solutions (do not implement yet)

1. Put **Billing / Buy deals** on the Agent home or a visible Owner row (not below the fold).
2. Add Billing to the avatar menu for owners.
3. Keep customer words **prepaid deals**, not credits.
4. Invited (non-owner) Agents should still not check out; this **owner** Agent must be able to pay without becoming Admin.

---

## 2. Tenant owner and role-update UI

**Data:** this user is owner.

**On the Agent home at 1366×768:** no role-update UI. The OWNER badge is the only owner signal. Change my role is in the DOM of the sidebar but **not in the viewport**.

**Avatar menu:** no Change my role.

**Settings:** Change my role is a tile under the in-page Organization heading, below Personal. On a laptop you scroll to it; it is not “visible” as a Settings → Organization menu.

`/settings/change-role` (direct URL) does show the identity picker. Ownership does not change when they switch identity.

If “updating roles” meant other people: **Users & Invites** is the same Owner/Settings-tile problem — not on the Agent home.

### Proposed solutions (do not implement yet)

1. Do **not** auto-promote this Agent to Admin.
2. Pin **Change my role** (and Billing) where the Agent already looks: avatar menu, and/or an Owner row **above** the fold, and/or a **My setup** sidebar link (identity plan §3.1).
3. Do not rely on “scroll the Settings page past nine Personal cards.”
4. Invited Agents must not get this strip.

---

## 3. AI Real Estate Coach — exists? necessary?

Unchanged and confirmed on the 1366 home screenshot: the banner is the **first** thing on the Agent dashboard.

| Piece | Reality |
|---|---|
| Dashboard “Add the AI Real Estate Coach” | Always shown. **Add AI Coach** / **See how it works** have **no `onClick`**. |
| Sidebar AI Coach | Not shown for this solo Agent (`team_id` null). |
| Product / checkout / backend coach | **None.** `AI_COACH_ENABLED = false` on AI Suggestions. `ai_coach_locked` always true. |

**Not necessary** for an independent Agent workspace. A dead primary CTA on the home page makes the workspace look unfinished.

**Proposed:** hide the banner until there is a real coach, or mark Coming soon without a live Add button.

---

## Independence gap (user-visible)

| Requirement | What this Agent owner sees |
|---|---|
| Own landing | Yes — `/dashboard/agent` |
| Specialized home | Coach upsell first; empty pipeline |
| Pay for deals | **Not visible** on the workspace |
| Change own role / run org | **Not visible** on the workspace at laptop size |
| Settings → Organization | **Not a real navigation path** |

---

## Suggested implementation order (when code work is approved)

1. Stop describing owner tools as “Settings → Organization.” Put **Change my role** and **Billing** in chrome that is on screen: avatar menu and a non-scrolled Owner strip (include Billing; it is missing there today).
2. Agent home: prepaid-deal chip + buy; remove or demote the coach banner.
3. Leave Admin-only jobs (AI Governance, ads, audit) off this identity.

---

## Additional findings (2026-09-07, beyond the original three)

Checked against the identity plan §3.1 / §2.4, this Agent owner’s live chrome at **1366×768**, and the APIs for `taytum.calah@minafter.com`. Still findings only. Product source was not changed.

These are **not** restatements of “no buy UI / no role UI / fake coach.”

### 4. Agent identity settings have no home in the Agent workspace

The plan’s Agent nav includes **My setup**. There is no such link. Identity config exists only as Personal tiles on `/settings` (Email & E-signature, My Playbook, My automation, My fee defaults, Email Templates). Those tiles work if you already opened Settings. They are not on the Agent home, not in the sidebar, not in the avatar menu.

Missing as a product surface (not merely buried):

- **Representation default** (Buyer / Seller / both). There is no settings field and no onboarding step. The wizard asks per deal every time.
- **My fee defaults** are this-browser `localStorage` only (`ve-wizard-last-fees`). They do not follow the account.
- **Writing style** is on Profile (reachable) and also on Admin AI Governance (not this identity). Fine if Profile is the home; it is not called out as Agent setup.

Day-one “connect email, set representation, set Trusted/You confirm, set fees” is not a first-class Agent flow. Onboarding is still a shared internal track (welcome / profile / Aime / inbox / e-sign). It never mentions representation. The finish screen tells an Agent to “create transactions later from Active Transactions,” not from their desk.

### 5. Settings shows Team Lead libraries this Agent cannot open

After Personal + Organization, Settings has a **Workspace** heading: “Shared configuration for everyone in your brokerage.” For this solo Agent owner the tiles are **Task Templates**, **Vendor Templates**, and **Team Playbook**.

- Visibility uses `teamLeadOrOwner` (owner counts as Team Lead).
- Those routes are `RoleRoute` Team Lead / Admin with **no** owner bypass.
- Clicking **Task Templates** returned this account to `/dashboard/agent`.

So Settings advertises Team Lead work, then dumps the Agent off the page. That is identity leak plus a broken card (the hub comments claim a card never leads to a dead end).

The APIs still admit the owner: `GET /task-templates` and `GET /teams` returned **200** because `require_role` still short-circuits for `is_tenant_owner`. Chrome hides Team Lead pages; the backend still treats the Agent founder as Team Lead for those libraries.

### 6. “My automation” writes the **tenant** posture, not “my files”

`PUT /api/v1/automation/settings` is `require_role(TeamLead, Admin)`, which **includes owner bypass**. This Agent owner’s PUT returned **200** and persisted `default_posture`. That is the intended solo alias (plan Phase 2B) while they are the only staff user.

After they invite a second internal person, the same page still writes the **tenant** default. There is no per-user posture. An Agent owner who stays Agent would keep a Team Lead/Admin write on everyone else’s automation. Scope snap (`ve_identity_scope_snap_v1`, default on) only shrinks **deal lists**, not this setting.

Needs You recovery for `library_send_off` is labeled “Open AI & Automation” and links to **`/admin/confidence`**. That is Admin-identity. This Agent cannot use it (`PUT /confidence/tenant` is 403). One Chrome pass that opened that URL ended on `/login` (session dropped), which is worse than a bounce.

### 7. Owner strip is incomplete even when you scroll the sidebar

Plan §2.4: Company, branding, billing, danger zone, invites. Live Owner group is only **Company**, **Users & Invites**, **Change my role**. **Billing** and **Branding** are Settings tiles only. **Delete Organization** is Settings-only.

At 1366×768 the sidebar also hides **Intelligence** (AI Suggestions, Email, Vendor Proposals, Analytics) in the same scroll well as Owner — below Workflow, above the pinned **+ New Transaction** / avatar. The Agent home therefore does not present Intelligence either, unless they notice the sidebar scrolls.

### 8. First-run copy still is not an originator desk

Empty action-queue copy (source): “Use this time to **prospect or chase referrals**.” No “open a deal / connect inbox / buy a prepaid deal.” The home’s first painted block is still the dead Coach banner. Analytics (source) still ships locked **AI Coach Pro** cards once overview data loads; this empty account’s Analytics page painted filters and a blank body on first load.

Guided tour for all internal roles (including Agent) says Settings holds “checklist templates, **integrations**, branding, billing, and **team setup**.” Integrations is Admin-only. Team setup is not this identity. The tour promises another role’s console.

### What this extra pass did **not** find

- This login is still Agent + owner; Admin identity APIs (ads, audit, tenant AI floors) stay 403.
- `/admin/users` **does** open for this owner, with **Invite user**. Invites work if they already know the URL or scroll Settings.
- Direct `/organization?section=billing` still has the buy UI after the wallet probe (200). Prepaid-deal purchase is buried, not missing from the product.
- Personal Connections / Playbook / My automation / My fees routes are allowed for Agent. They are just not part of the Agent chrome.
- Do **not** auto-promote this Agent to Admin to “fix” any of the above.
