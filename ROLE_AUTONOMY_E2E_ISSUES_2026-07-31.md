# Role-based account creation and autonomy — E2E test findings

**Date:** 2026-07-31
**Requested by:** Jake — "let users create an account for their role and then
operate the system freely and independently."
**Scope under test:** the public sign-up form, the onboarding wizard, the
invitation path, and what each of the eight roles can actually *do* once the
account exists (billing, transactions, team, workspace settings, invites).
**Companion document:** `ROLE_AUTONOMY_REMEDIATION_PLAN_2026-07-31.md`.

> **No source code was changed.** Every result below was produced by driving the
> shipped code as-is in a real Chrome browser against a fresh local stack. The
> only non-product action was confirming each new account's email address
> through the Supabase admin API, because the local project has email
> confirmation enabled and this machine cannot read the test mailbox — that is
> exactly what clicking the link in the confirmation email does.

---

## 1. Environment

| Piece | Value |
| --- | --- |
| Backend | fresh `uvicorn app.main:app` on `127.0.0.1:8021` (the long-lived `:8000` / `:8001` instances serve older code) |
| Frontend | fresh `vite` on `localhost:5190` with `VITE_API_BASE_URL=http://localhost:8021` |
| Browser | system Chrome via puppeteer-core, real forms, real clicks |
| Stripe | test mode, `pk_test` / `sk_test`; checkout reached for real |
| Deal fee | `$49.00`, first deal free, 10+2 bundle offer active |
| Accounts created | 15 (4 self-sign-up founders, 2 clean-room founders, 8 invited members, 1 role-relabel founder) |

Harness: `c:\Projects\_tools\e2e\role\` (`r01`…`r07`).
Screenshots and raw JSON: `c:\Projects\_shots\roles\`.

### What was run

| # | Harness | What it does |
| --- | --- | --- |
| 1 | `r01_signup.mjs` | Reads the sign-up role dropdown, registers one founder per offered role through the real form, walks the real onboarding wizard, records the landing surface. Also asks the server for the four roles the form does not offer. |
| 2 | `r02_capabilities.mjs` | Per founder: nav, Settings hub, Billing pane, a real "Buy one deal" click, the New-Transaction affordance, and 15 server gates called with that user's own session token. |
| 3 | `r03_routes.mjs` | 47-route direct-URL sweep per role — separates "cannot" from "cannot find". |
| 4 | `r04_invited.mjs` | The Admin founder invites one member of every role; each invite is accepted through the real `/invite/<token>` form; the same capability sweep is run on each member. |
| 5 | `r05_clean_hosts.mjs` | Two brand-new workspaces used to measure the staff-seat ceiling without contamination, and to provision the staff roles R04 could not reach. |
| 6 | `r06_focus.mjs` | Section-by-section read of the unguarded `/organization` route for eight different roles; the onboarding Step-2 role relabel. |
| 7 | `r07_invite_modal.mjs` | Which roles can reach the real Invite modal at all, versus which ones the server lets create an invitation. |

---

## 2. The measured role matrix

**Self-sign-up founders** (all four are the tenant owner):

| Account type at sign-up | Stored role | Lands on | Sidebar items | Settings cards | Can buy a deal |
| --- | --- | --- | --- | --- | --- |
| Agent *(default)* | `Agent` | `/dashboard/agent` | 16 | 19 | **yes** — click reached Stripe checkout |
| Team Leader | `TeamLead` | `/dashboard/team` | 19 | 19 | **yes** |
| Transaction Coordinator | `TransactionCoordinator` | `/dashboard/agent` | 16 | 19 | **yes** |
| Admin | `Admin` | `/dashboard/admin` | 20 | 19 | **yes** |

**Invited members** (never the owner):

| Role | Lands on | Sidebar | Settings cards | Buy a deal | Invite anyone | Reach `/admin/users` |
| --- | --- | --- | --- | --- | --- | --- |
| Agent | `/dashboard/agent` | 16 | 6 | **403** | API 201, **no UI** (R-06) | **`/unauthorized`** |
| TransactionCoordinator | `/dashboard/agent` | 16 | 6 | **403** | API 201, **no UI** (R-06) | **`/unauthorized`** |
| TeamLead | `/dashboard/team` | 19 | 10 | **403** | yes | yes |
| Admin | `/dashboard/admin` | 20 | 18 | yes | yes | yes |
| Attorney | `/dashboard/attorney` | 6 | 5 | **403** | **403** | `/unauthorized` |
| ForSaleByOwner | `/fsbo` | 5 | — | **403** | **403** | `/unauthorized` |
| Vendor | `/portal/vendor` | 3 | — | **403** | **403** | `/unauthorized` |
| Client | `/client/home` | 5 | — | **403** | **403** | `/unauthorized` |

Sidebar counts for the three portal roles are read from the screenshots
(`r04-12-vendor-landing.png` and siblings) because those layouts do not use the
`aside nav` structure the harness counts: Vendor = Dashboard, Document
Requests, My Uploads; Client = Home, Timeline, Documents, Payments, Agent Info;
FSBO = Dashboard, My Properties, Documents, Payments, Messages.

---

## 3. What actually happens with the reported problem

Jake's example was "create an account as *agent* and you cannot buy credits."

**Measured: it does not reproduce for a self-sign-up Agent.** A founder who
picks Agent gets `is_tenant_owner = true`, the Billing card appears in their
Settings hub, the Billing pane renders **Buy one deal** and **Buy bundle**, and
clicking **Buy one deal** navigated to a live Stripe checkout session.
`POST /billing/credits/checkout-session` returned `200`.

**It reproduces exactly for an Agent who was *invited*** into someone else's
workspace: the same endpoint returns
`403 — "Only a workspace owner or admin can pay for deals."`

So the real defect is not "the Agent role cannot pay." It is that **role and
authority have been wired as two separate systems, and the UI only reads one of
them.** The backend already routes authority through workspace ownership
(`require_role` short-circuits on `is_tenant_owner`, `core/auth.py:160`). Large
parts of the frontend still read `role === 'Admin'`. Every place the two
disagree is a place where a founder is refused something the server would have
allowed — and that is what "not fully autonomous" feels like in use.

The single clearest instance is below (R-01) and it is worth looking at the
screenshot before reading anything else:
`c:\Projects\_shots\roles\r06-owner-agent-org-company.png`.

---

## 4. Findings

Severity: **S1** blocks a role from operating · **S2** capability exists but is
unreachable or unexplained · **S3** correctness/consistency · **S4** polish.

### Cluster A — the owner is not treated as the owner

#### R-01 · S1 · A non-Admin founder cannot rename their own organization
`/organization?section=company`, signed in as the **Agent founder** whose own
sidebar badge reads `Agent · OWNER`, renders the Organization-name field
read-only with the help text:

> "Only an Admin can change this. **Ask your workspace owner** if it needs updating."

They *are* the workspace owner. There is no one to ask.

- Measured: `editableInputs = 0`, no Save button, for the Agent, TeamLead and
  TC founders. The Admin founder gets 1 editable input and a Save button.
- The server would have accepted it: `PATCH /tenants/current` is
  `require_role(UserRole.ADMIN)` (`api/v1/tenants.py:153`) and `require_role`
  returns early for the owner (`core/auth.py:160`).
- Root cause: `OrganizationPage.tsx:82` —
  `canEditTenant = Boolean(user && hasMinimumRole(user.role, 'Admin'))`, with no
  `is_tenant_owner` term.
- Evidence: `r06-owner-agent-org-company.png`, `r06-owner-admin-org-company.png`.

#### R-02 · S1 · The same founder *can* delete the whole organization
On `?section=danger` the Agent founder gets a live **Delete organization**
button (`canSeeDanger` is correctly owner-based, `OrganizationPage.tsx:109`).

The workspace owner may destroy the workspace but may not edit its name. This is
the asymmetry that makes R-01 a bug rather than a policy.

#### R-03 · S1 · Branding is locked to the founder for the same reason
`?section=branding` for Agent / TeamLead / TC founders: **Upload logo** is
disabled, no **Save branding**. `BrandingPane` receives the same
`canEdit={canEditTenant}` flag. Admin founder: 4 editable inputs, 3 buttons.

#### R-04 · S2 · The sidebar hides every management surface from a non-Admin founder
`dashboardShellConfig.ts` keys `sidebarSections` on the **role string only**:

| Role | sections |
| --- | --- |
| Agent / TransactionCoordinator | kpis, deals, workflow, payments, vendors, intelligence, settings |
| TeamLead | …+ **team** |
| Admin | …+ **team**, **admin** |

The 47-route sweep (R03) proves the Agent founder opens **all** of these with
verdict `ok`: `/team`, `/admin/users`, `/admin/teams`, `/admin/task-templates`,
`/admin/team-settings`, `/admin/communications`, `/admin/vendor-templates`,
`/admin/audit-logs`, `/admin/confidence`, `/admin/integrations`,
`/admin/advertising`, `/admin/payment-access`.

The product is internally inconsistent about the same permission: the Settings
hub *does* apply the owner bypass (`settingsCards.ts:59-62`, all four founders
see the same 19 cards), while the sidebar does not. A founder can therefore
reach Team management by searching Settings but never by navigating.

#### R-05 · S2 · Twelve more surfaces gate on `role === 'Admin'` with no owner term
Each is a control a non-Admin founder is shown as missing or disabled although
the server would allow the action:

| File | Line | Flag |
| --- | --- | --- |
| `pages/organization/OrganizationPage.tsx` | 82 | `canEditTenant` |
| `pages/users/AdminUsersListPage.tsx` | 56 | `isAdmin` |
| `pages/admin/AdminTeamsPage.tsx` | 54 | `isAdmin` |
| `pages/admin/AdminTeamSettingsPage.tsx` | 70 | `isAdmin` |
| `pages/admin/TaskTemplateListPage.tsx` | 102 | `isAdmin` |
| `pages/admin/CommunicationAuditPage.tsx` | 77 | `isAdmin` |
| `components/team/TeamMembersTable.tsx` | 110 | `isAdmin` |
| `components/team/ManageTeamMembersPanel.tsx` | 68 | `isAdmin` |
| `pages/TeamPage.tsx` | 483, 496 | role-change controls |
| `pages/vendors/VendorListPage.tsx` | 88 | `canDelete` |
| `pages/EmailTemplatesPage.tsx` | 75 | `isAdminLike` |
| `pages/transactions/TransactionListPage.tsx` | 426 | admin-scope filter |
| `components/wizard/NewTransactionWizard.tsx` | 3309, 3321, 5812 | admin branches |
| `layouts/AppLayout.tsx` | 663, 720 | `teamScopedSidebar`, `isAdmin` |

#### R-06 · S3 · An invited Agent / TC can invite people through the API but has no UI for it
`create_invitation` accepts `AGENT, TEAM_LEAD, ADMIN, TRANSACTION_COORDINATOR`
(`api/v1/invitations.py:127-132`), and `inviteableRolesFor('Agent')` returns
`['Agent', 'Client', 'ForSaleByOwner', 'Vendor']`. But the only screen hosting
the Invite modal, `/admin/users`, is guarded `ProtectedRoute requiredRole="TeamLead"`
(`App.tsx:750`), and the Settings hub shows the "Users & Invites" card only to
TeamLead-or-above/owner.

Measured (R07), for both an invited **Agent** and an invited **Transaction
Coordinator**: `POST /invitations/` with `role: "Client"` → **201**;
`/admin/users` → **`/unauthorized`**; no "Users & Invites" card in Settings. The
same probe run as the Agent *founder*, the TC *founder* and an invited *Team
Lead* reaches `/admin/users` normally. The capability is real for the two
member roles and completely unreachable from the interface.

#### R-07 · S3 · Attorney is offered invite targets it can never use
`inviteableRolesFor` falls through to `default: return portal` for Attorney,
Vendor, FSBO and Client — i.e. the matrix says an Attorney may invite Client /
FSBO / Vendor. The backend's `require_role` list excludes Attorney, so every
such call returns **403**. Measured: invited Attorney, `POST /invitations/` →
`403 "You do not have permission to perform this action."`

---

### Cluster B — paying for the product

#### R-08 · S1 · No member other than the owner or an Admin can pay, and the dead-end is silent
`can_manage_billing = is_tenant_owner or role == Admin or is_platform_admin`
(`api/v1/billing_credits.py:64-69`). Measured `403` on
`POST /billing/credits/checkout-session` for invited Agent, TransactionCoordinator,
**TeamLead**, Attorney, FSBO, Vendor and Client.

The Billing pane degrades honestly — *"A workspace owner or admin handles
payments for this account."* — but offers **no action**. The escalation endpoint
`POST /billing/credits/notify-admin` exists and works (measured **202** for every
role tested) and no surface in the product calls it from the Billing pane. A
coordinator who needs a deal paid for has to leave the product and send a
message some other way.

Whether a **Team Leader** should be able to pay is a product decision, not a
bug — but it is currently a decision nobody made explicitly, and it is invisible.

#### R-09 · S1 · `/organization` has no route guard — portal users read workspace billing
`App.tsx:743`:

```tsx
<Route path={ROUTES.ORG_SETTINGS} element={<OrganizationPage />} />
```

No `RoleRoute`, no `ProtectedRoute requiredRole`. Measured in the browser, an
invited **Client**, **Vendor** and **FSBO seller** each opened
`/organization?section=billing` *inside their own portal shell* and read the
brokerage's:

- per-deal fee (`$49.00 per deal`),
- prepaid-deal balance,
- the credit ledger history rows.

Screenshot: `r06-inv-vendor-org-billing.png` — the Velvet Elves **Vendor
Portal** chrome with the brokerage's Billing page inside it. A vendor is an
outside company, not an employee.

`?section=company` leaks the organization name, the plan tier and the seat
count to the same audience; `?section=danger` falls back to rendering that same
Company card, so it leaks too. Only the destructive control is correctly hidden.

#### R-10 · S1 · `GET /billing/credits/wallet` has no role gate
`api/v1/billing_credits.py:118-145` depends only on `get_current_user`.
Measured **200** for Client, Vendor and FSBO — returning `balance`,
`fee_cents`, `first_deal_free_remaining` and the last 8 ledger entries of the
host workspace. This is the data source behind R-09 and needs fixing at the
endpoint, not only in the router.

---

### Cluster C — the seat ceiling

#### R-11 · S1 · A self-sign-up workspace is capped at 5 staff and cannot lift the cap itself
Measured on two clean workspaces: `plan = "trial"`, `seat_limit = 5`,
`staff_seat_count = 1` at creation. Invites 1-4 (Agent, TeamLead, TC, Admin)
returned **201**; invite 5 (Attorney) and invite 6 (Agent) returned
**409 — "You've reached the staff seat limit on the trial plan."**

The only statement of this anywhere in the product is on
`/organization?section=company`:

> "During the beta your plan is set by your Velvet Elves account team. Online
> plan changes arrive once pricing is finalized."

That is honest, and it is also the exact opposite of "operate independently."
A Team Leader who signs up to run a 12-agent team hits a wall at 5 and the
product's answer is to contact the vendor.

#### R-12 · S2 · The seat ceiling is invisible on the screen where it bites
`/admin/users` — the screen with the **Invite user** button — never mentions
seats or the plan (measured: no match for `/seat/i` or `/plan/i` in the page
text on two clean workspaces). The count is shown only on the Company settings
page, which is a different section of a different route. Users discover the cap
as a 409 at the moment of inviting.

#### R-13 · S3 · Pending invitations consume seats with no visible accounting
The DB seat-check counts active staff **plus** unexpired, unrevoked, unused
staff invitations (`seat_service.py:82-95` and the
`create_invitation_with_seat_check` function). Four invitations that nobody ever
accepts will lock a founder out of inviting anyone else, and the Users page
shows "Pending invitations 4" without connecting it to the cap.

---

### Cluster D — sign-up and role selection

#### R-14 · S1 · Four of the eight roles cannot create an account at all
The dropdown offers exactly `["Agent", "Team Leader", "Transaction Coordinator",
"Admin"]` (default **Agent**). Asking the server for the other four:

| Requested role | Response |
| --- | --- |
| `Attorney` | 422 |
| `ForSaleByOwner` | 422 |
| `Vendor` | 422 |
| `Client` | 422 |

with detail *"You can sign up as an Agent, Team Leader, or Transaction
Coordinator. Other account types join a transaction by invitation."*
(`SELF_SIGNUP_ROLES_NOW`, `models/enums.py:180`).

Against Jake's request — *users pick their role at sign-up and then operate
independently* — the answer today is **4 of 8 can sign up, and of those 4 only
the founder is autonomous.**

#### R-15 · S3 · The rejection message contradicts the form
The message names three roles. The form offers four and the server accepts the
fourth (`Admin`). Anyone reading the error is told something the product does
not do.

#### R-16 · S3 · "Admin" is offered to the public as a professional identity
`Admin` is a permission level, not a job a real-estate professional would pick.
It also silently changes the product: an Admin founder's onboarding **drops the
E-signature step** (`ESIGN_ROLES = Agent, TransactionCoordinator, TeamLead,
Attorney`, `OnboardingWizard.tsx:90-95`) — measured 4 wizard steps for Admin
versus 5 for the others — so a founder who picks Admin is never offered DocuSign
during setup even though they will run their own deals. The prior design
document (`SIGNUP_ROLE_SELECTION_AND_ONBOARDING_REMEDIATION_PLAN.md §2`)
explicitly excluded Admin from the self-sign-up list; the shipped code re-added
it "handy for testing" (`utils/accountTypes.ts:9-11`).

#### R-17 · S3 · The role choice never explains what it changes
Neither dropdown says what a role does. Measured consequences a user cannot
predict: TransactionCoordinator lands on `/dashboard/agent` (the *Agent*
dashboard) with a 16-item sidebar identical to Agent's; TeamLead gains a Team
group plus an "AI Coach — Locked" teaser; Admin gains Oversight. Picking wrong
is invisible until later.

#### R-18 · S4 · Stale contract in the wizard source
`OnboardingWizard.tsx:184-188` still documents *"Role is whatever was assigned at
signup (founder→Admin) … It is NOT user-pickable here"*, directly above a
`ProfileStep` that renders an editable role Select. The behaviour is correct;
the comment describes the previous design.

**Verified working, no defect:** the Step-2 relabel. A founder who signed up as
Agent switched to Team Leader on Step 2 — `PUT /users/{id}/role` succeeded,
ownership was preserved (`is_tenant_owner` still true), the stepper rebuilt from
4 to 5 steps live, and the founder landed on `/dashboard/team`.

---

### Cluster E — the connected roles are dead ends by construction

#### R-19 · S2 · Attorney, FSBO, Vendor and Client have no independent existence
Each can only be created by an invitation into somebody else's workspace, is
never the owner, and therefore inherits every restriction above. Measured:

| Role | Sidebar | Own settings route | Create anything | Pay | Invite |
| --- | --- | --- | --- | --- | --- |
| Attorney | 6 items, matter-driven | `/settings/*` (5 cards, no Email Templates) | no | 403 | 403 |
| ForSaleByOwner | 5 items | `/settings/account` **redirects to `/fsbo`** | no | 403 | 403 |
| Vendor | 2 items | redirects to `/portal/vendor` | no | 403 | 403 |
| Client | 5 items | redirects to `/client/home` | no | 403 | 403 |

For the three portal roles, `/settings/account` silently bounces to their portal
home with zero editable inputs; identity editing lives only in the account
modal reached from the sidebar footer. A tester following "go to Settings →
Profile" finds nothing.

#### R-20 · S3 · A fresh workspace gives the portal roles nothing to do
An invited Vendor lands on a portal reading `0 Open Requests · 0 Date Requests ·
0 Your Uploads`; an invited FSBO seller on `0 My Properties`; an invited Client
on `0 Transactions`. That is honest, but combined with R-19 it means these four
roles cannot be evaluated at all except as passengers in a deal somebody else
created — which is the opposite of the autonomy Jake asked for.

---

## 5. What is genuinely good — do not regress it

- **The backend owner anchor is right.** `is_tenant_owner` is computed in
  `get_current_user`, in every token builder (register / login / refresh), and
  honored in `require_role`, `require_team_access`,
  `list_accessible_transaction_ids`, `require_transaction_access`, the
  invitation grant check, and the billing gate. The model is sound; the UI has
  not caught up.
- **The owner cannot be locked out or demoted.** `PUT /users/{id}/role` refuses
  to change the owner's role for anyone but the owner, and the owner's own
  relabel is bounded to the self-operating set.
- **The Settings hub already does it correctly** (`adminOrOwner`,
  `teamLeadOrOwner`) and is the pattern the rest of the app should copy.
- **The Step-2 relabel works end to end**, including the live stepper rebuild.
- **Billing degrades honestly** for non-managers instead of throwing.
- **The Danger zone is correctly owner-gated** even on a forged deep link.
- **Zero page errors** across every role tested; 1-4 console warnings per role,
  none functional.

---

## 6. Test data left behind

All accounts use `@mailinator.com` addresses with the prefixes
`ve.r1.`, `ve.r2.`, `ve.s1.`, `ve.f1.`, `ve.gate.`, `ve.roleprobe.` and
`ve.deny.`. They live in 8 test tenants (`Agent Test Realty`, `Team Leader Test
Realty`, `Transaction Coordinator Test Realty`, `Admin Test Realty`, `Seat Test
A`, `Seat Test B`, `Relabel Realty`, `Probe Realty`). Roughly 20 unaccepted
invitations remain pending in those tenants. Remove with a delete on
`users.email LIKE 've.%@mailinator.com'` plus their tenants and invitation rows
when the environment is next reset. Two Stripe **test-mode** checkout sessions
were opened and abandoned; nothing was charged.
