# Team Lead and Transaction Coordinator workspaces — findings

**Date:** 2026-09-08  
**Status:** Review only. No product source was changed by this document.  
**App / API verified:** `http://127.0.0.1:5173` · `http://127.0.0.1:8000`  
**Viewport:** 1366×768  
**Artifacts:** `aime_automation_qa/artifacts_tl_tc_workspace_review/`  
**Plans in scope:** `ROLE_IDENTITY_INDEPENDENT_WORKSPACE_PLAN_2026-09-03.md` §3.2–3.3; `OWNER_INDEPENDENT_WORKSPACE_COMPLETION_PLAN_2026-09-07.md` (owner jobs on the founder’s own chrome)

This document does **not** ask Team Lead or Transaction Coordinator workspaces to look like the Agent workspace. It asks two things that must both be true:

1. A **primary tenant owner** can run the company from the workspace they signed up for — billing, prepaid deals, invites, company, change-my-role — without becoming Admin and without hunting through a buried Settings group.
2. Each identity keeps **features of that job**: Admin, Team Lead, Transaction Coordinator, and Agent are four products. Ownership is a badge on the same person, not a reason to clone another role’s desk.

---

## 0. How to read the findings

| Layer | Question | Pass looks like |
|---|---|---|
| **A — Owner independence** | Can this founder, *as Team Lead or as TC*, pay, invite, and change identity on day one from *their* home? | Billing, Users & Invites, and Change my role are reachable from Team Command / File Desk chrome (home, avatar, or an in-role owner strip). They never have to open Admin Console or switch role to do those jobs. |
| **B — Role product** | Does this desk do *this* job, and only this job? | Team Lead: team blockers, coverage, playbook, invite into *this* team. TC: file intake, documents, tasks, vendors, dates. Neither is a reskin of Solo Agent. Neither is Admin Console. |

**Severity**

- **Flaw** — the feature exists but is wrong for the role, misplaced, broken, or identity-collapsing.
- **Missing** — the role (or the owner badge on that role) needs it and does not have it on the workspace.
- **Unnecessary** — it is on the desk and should not be, or it duplicates another surface.

Accounts used for the live pass (fresh local password signups, both `is_tenant_owner: true`):

| | Team Lead founder | TC founder |
|---|---|---|
| Email | `qa.tl.owner.20260908@minafter.com` | `qa.tc.owner.20260908@minafter.com` |
| `role` | `TeamLead` | `TransactionCoordinator` |
| `team_id` | minted at signup | `null` |
| Landing | `/dashboard/team` · **Team Command** | `/dashboard/coordinator` · **File Desk** |
| Wallet | HTTP 200, `can_manage_billing: true`, prepaid 1, $49 | same |

Do **not** auto-promote either account to Admin. Do **not** reintroduce seat caps.

---

## 1. What is already role-correct

Keep these. They are the start of independent, tailored workspaces — not a reason to stop.

### 1.1 Team Lead

- Lands on **Team Command**, not Solo Agent and not Admin Console.
- Signup **mints a team** and attaches the founder (`lead_user_id` + `users.team_id`). Team Command is not an empty identity.
- Brand string is **Team Command**. Primary CTA is **+ New Transaction**. **Invite to team** is on the dashboard (identity-gated; Agents do not get this button).
- Sidebar **Team** group: Team Overview + Teams. **New team** on the Teams page is Admin-only (creating a second team can wait — that is correct).
- Settings **Workspace** cards for Task Templates, Vendor Templates, and Team Playbook **render and open** for Team Lead identity. They are hidden for TC. That split is right.
- Dashboard Communication log goes to **`/admin/communications`** (team audit), not the personal Email queue.
- `PUT` tenant automation posture returns **200** as Team Lead identity (this is the Team Lead job, not a borrowed Admin page).
- Representation card is **hidden** (Agent-only). Fake **AI Coach** nav / purchase modal / dashboard banners are **gone**.
- Onboarding recommends **Invite someone to your team**, then Team Command.

### 1.2 Transaction Coordinator

- Lands on **`/dashboard/coordinator`**, brand **File Desk** (founder with `team_id` null).
- Primary CTA is **+ Open file**, not “New Transaction.”
- **No** Team sidebar group. **No** Invite to team. **No** Task / Vendor Templates or Team Playbook cards.
- Representation is **hidden**. Empty-desk copy is file-desk (“What to chase” / open a file to start intake), not “prospect or chase referrals.”
- Communication log goes to **`/ai-emails`** (this identity’s mailbox), not the Admin audit.
- Solo-staff `PUT` automation returns **200** (one-person workspace alias). After a hire, tenant write is supposed to stop for TC — that hire-guard is the correct *identity* rule; the *copy* that tells them to become Admin is not (see §3.2 and §4.2).
- Onboarding recommends **Open your first file**, then File Desk.

### 1.3 Owner badge in data (both)

`is_tenant_owner` is true. Direct URLs work: Billing (`/organization?section=billing`), Change my role, Users & Invites. The Settings hub group is labeled **Owner**, not Organization. Buy prepaid deals works once you are on the billing pane. The wallet exists. The owner job is implemented — it is just not on the workspace they actually use.

---

## 2. Layer A — owner independence on *this* workspace

This layer is the same *job* for every founder. The chrome that must carry it is **not** the same: it has to sit on Team Command for a Team Lead and on File Desk for a TC. Copying Agent’s home widgets is not the fix.

### Missing

| ID | Gap | Evidence |
|---|---|---|
| **A1** | **Billing / prepaid deals** are not on Team Command or File Desk, not in the visible sidebar, not in the avatar menu. | Live: `ui.s1.billing_on_home_or_nav` ABSENT; avatar Billing ABSENT. Wallet `can_manage_billing: true` on both accounts. |
| **A2** | **Change my role** is not on home, sidebar, or avatar. | Live: `ui.s2.change_role_on_home_or_nav` ABSENT. Page exists at `/settings/change-role`. |
| **A3** | **Users & Invites** (hire anyone into the tenant) is not in nav. Team Lead has a dashboard **Invite to team** (role feature). TC has **no** invite chrome at all. Owner hiring is still Settings-only. | Live: `ui.s2.users_invites_on_nav` ABSENT. |
| **A4** | The only discovery path is **avatar → Settings**. Personal tiles fill the first screen. The **Owner** heading sits at about **y = 631 of 768**. Billing / Change my role / Users sit under it — below the laptop fold unless you already know to scroll. | Live screenshots `*_03_settings.png`; `ui.s2.billing_in_viewport_1366` / `change_role_in_viewport_1366` = NO. |

A Team Lead founder can run Team Command and still not pay or relabel themselves. A TC founder can run File Desk and still not hire or buy deals. That is not “they need Agent features.” It is that **ownership is not attached to the role workspace they were given.**

Settings remaining the catalog for owner jobs is fine. Day-one independence fails when the catalog is off-screen and the avatar only offers Settings / Help / Log Out.

### Flaw (owner copy that collapses identity)

| ID | Flaw |
|---|---|
| **A5** | Shared automation copy treats every owner like an Agent who must become Admin after a hire. `SettingsMyAutomationPage` (all owners): *“After you invite staff, tenant posture becomes Admin work.”* `AutomationPostureSection` when write is locked: *“Tenant automation is Admin work. Switch your role to Admin, or invite an Admin.”* Backend `can_write_tenant_automation` **keeps Team Lead write after a hire**. Telling a Team Lead owner to switch to Admin is identity collapse. Telling a TC owner the only recovery is to *become* Admin (rather than invite an Admin / Team Lead and stay TC) is the same collapse. |

### Not in scope for this layer

- Do not pin a generic “Owner” sidebar group as the only answer if that IA was already rejected. The requirement is **reachability from this role’s chrome** (avatar items, a home chip, or an in-role strip on Team Command / File Desk).
- Do not put Advertising, Payment Access, AI Governance, or Audit Log on Team Lead or TC. Those stay Admin identity.

---

## 3. Layer B — Team Lead workspace (Team Command)

Job: see the team’s blockers, cover gaps, set the team playbook, invite Agent/TC into *this* team. Not “Admin with a team dashboard.” Not “Solo Agent with a team_id.”

### 3.1 Flaws

**B-TL1 — Team Command is not a Team Lead product.**  
`getLandingRoute` sends every **Agent with `team_id`** to `/dashboard/team`. `getBrandDescriptor` also labels that Agent **Team Command**. The page is `TeamLeaderDashboardPage`: intervention queue (“Where to step in today”), Agent board, team financials, “coach an agent.” Only **Invite to team** and the communication-audit URL are identity-gated. An invited Agent therefore sits at a **manager desk**. That both steals the Team Lead home and gives Agents a job they did not pick.

**B-TL2 — The Team Lead’s own Team nav is below the fold.**  
At 1366×768 the first paint is Dashboard / Deals / Workflow / + New Transaction. **Team Overview** (~y 795) and **Teams** (~y 826) sit under the fold, then Intelligence under that. The specialized nav for this identity is the part you cannot see without scrolling the sidebar.

**B-TL3 — “Invite to team” on Team Command opens the org Users page.**  
The button `navigate`s to `ROUTES.ADMIN_USERS` with **no** `team_id`. The Teams page already has a team-scoped **Invite to team** modal (`InviteUserModal` locked to the selected team). Home CTA and team CTA are two different products with the same label. For a founder this often “works” because they are also owner; it is still the wrong surface for the Team Lead job (invite into *this* team from Team Command).

**B-TL4 — Three overlapping “who is on the team” surfaces.**  
Team Command has an Agent board. **Team Overview** (`TeamPage`) is the former brokerage production snapshot (`/api/v1/admin/brokerage/overview`) plus roster. **Teams** is the in-place roster + invite + manage members. A Team Lead founder gets three people/production pages, two of them named like Admin leftovers, and the useful one (Teams) is below the fold.

**B-TL5 — Team identity config is not on Team Command.**  
Plan 3B: playbook, task/vendor overlays, and **team automation** should be reachable from this workspace. Today they are Settings Workspace / Personal tiles only. A Team Lead who never opens Settings never sets the playbook that defines the identity.

**B-TL6 — Team Lead automation copy is Agent-founder copy.**  
See **A5**. The API is correct (`TeamLead` always may `PUT`). The UI still narrates “this becomes Admin work when you hire.”

**B-TL7 — Communication audit is an Admin URL with no Team Lead nav.**  
Dashboard quick action → `/admin/communications`. Sidebar **Oversight** (Communication Audit, Audit Log) is Admin-only. Team Lead can open the audit from the desk but cannot find it as a first-class Team Lead item. The page header/comments still describe **Admin → Communication audit**. Audit **Log** should stay Admin; communication review for the team is Team Lead work.

**B-TL8 — Coach-as-product language is still on the desk.**  
The fake Coach purchase CTA is gone. Remaining:

- Empty intervention: *“Good time to coach proactively or review pipeline.”*
- Ask Velvet Elves hint: *“Summarize team risk, **coach an agent**, or open the next file…”*
- Drift row: **Coaching needed**
- Unused `TeamRailFeeds.tsx` still builds prompts like *“needs immediate pricing-coach support today”* (dead code, but it is the old fake-coach feed)

**B-TL9 — Agent drill-down contact actions are stubs.**  
Email `mailto:?subject=…&to=` (empty), Call `tel:`, Text is a no-op button. A Team Lead “check in with this agent” tool that cannot address the agent.

**B-TL10 — Shared Agent workflow chrome on a team desk.**  
Sidebar **My Task Queue** (personal), **All Documents** still commented as “the Agent workflow queue,” Deals → **Clients** as origination chrome. Coverage is a Team Lead job; the queue labeling is still “my Agent list.”

### 3.2 Missing

| ID | Missing feature | Why it is Team Lead, not Agent |
|---|---|---|
| **B-TL11** | Owner jobs on Team Command chrome | Layer A on *this* home. |
| **B-TL12** | Playbook / task templates / vendor templates / team automation **from Team Command** | Identity config for “I run a team’s files.” |
| **B-TL13** | A coverage + invite pair that stays on this desk | Plan: New Transaction (coverage) **and** invite into this team. Invite exists but routes away; there is no “open a file for coverage” affordance distinct from Agent origination. |
| **B-TL14** | Communication audit in Team Lead nav | Team coaching / coverage, not Admin Oversight. |
| **B-TL15** | After-hire copy that says **you still set team posture**; Admin sets tenant floors / kill switches | Distinct from Agent/TC hire-guard. |

### 3.3 Unnecessary

| ID | What to remove or stop sharing |
|---|---|
| **B-TL16** | **Team Command as the teamed-Agent landing and brand.** Agents on a team should keep an Agent desk with team *scope*, not a manager console. |
| **B-TL17** | **Team Overview as a third roster/production page** while Agent board + Teams already exist. Keep one people surface (Teams) and one operational board (Team Command). |
| **B-TL18** | **`TeamRailFeeds.tsx`** — unused; still encodes fake coach prompts. |
| **B-TL19** | Remaining **AI Coach** wording (empty states, Ask AI hint, drift label). |
| **B-TL20** | Settings Workspace blurb *“Shared configuration for everyone in your brokerage”* on Task Templates / Team Playbook for a Team Lead — those are **this team’s** libraries, not Admin tenant policy. |

Admin-only items correctly **absent** from this workspace (keep them absent): Advertising, Payment Access, AI Governance, Audit Log, New team, Document Templates library.

---

## 4. Layer B — Transaction Coordinator workspace (File Desk)

Job: keep the file moving — documents in, tasks cleared, vendors and dates on track. Origination is secondary. Must not become a skin of Solo Agent. Must not become Team Command because they joined a team.

### 4.1 Flaws

**B-TC1 — File Desk is still Solo Agent with a copy swap.**  
`CoordinatorDashboardPage` is one line: `<SoloAgentDashboardPage identity="coordinator" />`. Coordinator-specific UI is:

- KPI label swap: Active files ↔ Pending GCI  
- Hero: “File desk / What to chase” vs “Today / Action queue”  
- Empty-state sentence  

Everything else is the Agent desk: **Pipeline volume**, **YTD closings**, **Pending GCI** still on the strip (with a **DollarSign** icon on Active files), **Priority transactions**, **Portfolio health**, `PaymentsWidget scope="me"`, Agent Ask AI hint (*“Draft emails, chase signatures, explain risk, summarize a file.”*), `useAgentDashboard()` payload. The identity plan named this collapse explicitly.

**B-TC2 — Teamed TC wears Team Lead’s brand.**  
Landing stays `/dashboard/coordinator` (good). `getBrandDescriptor` still returns **Team Command** when a TC has `team_id`. An invited coordinator would run File Desk under a Team Lead label. Founder TC in this pass had `team_id` null, so they saw File Desk — the bug is waiting for the first hire onto a team.

**B-TC3 — Nav is the Agent internal shell.**  
Same Deals group (Active, Drafts, **Clients**, Contacts), same Intelligence (AI Suggestions, Email, Vendor Proposals, Analytics). Plan §3.2 wanted emphasis on **All Documents, Needs You, Task Queue, Calendar, Vendors, Contacts** — not listing-side / origination chrome. Clients + GCI + Analytics as first-class TC nav is the Agent product sitting on File Desk.

**B-TC4 — All Documents is still documented and built as the Agent workflow queue.**  
Same page, same comment, no coordinator intake emphasis (no “complete file” checklist, no intake-first empty state).

**B-TC5 — Owner automation recovery tells a TC to become Admin.**  
Hire-guard (TC loses tenant `PUT` after a second staff user) is the right **identity** rule. The **owner** recovery must not be “switch your role to Admin.” Stay TC; invite an Admin (or a Team Lead for team posture); keep per-file override.

**B-TC6 — API still serves Team Lead libraries to a TC owner.**  
Live `GET /task-templates` **200** while the Settings cards are hidden. UI is honest; the read API still treats owner as a library audience. Not a bounce-CTA, but it is the old owner-bypass leak on a role that must not manage those libraries.

### 4.2 Missing

From plan §3.2 — still not a coordinator product:

| ID | Missing | Notes |
|---|---|---|
| **B-TC7** | A **real File Desk landing** (own widgets / payload), not `SoloAgentDashboardPage` | Largest remaining TC hole. |
| **B-TC8** | **Intake documents** as a primary action next to + Open file | Plan: Open file **plus** intake. |
| **B-TC9** | **Default document checklist** (what “complete file” means on this desk) | Identity config. |
| **B-TC10** | **Vendor defaults** (title, lender, inspector) for files they open | Identity config. |
| **B-TC11** | **Queue-dense notifications** (coordinators live in queues; Agents live in dates) | Notifications card exists but is generic. |
| **B-TC12** | Owner jobs on File Desk chrome | Layer A. A TC founder has **zero** invite control on the desk; they cannot hire a closer or an Admin without Settings. |
| **B-TC13** | Nav / KPI emphasis on documents, tasks, vendors, dates — not GCI / YTD / Clients | Tailoring, not cloning Agent. |

### 4.3 Unnecessary (on this identity)

| ID | Remove or keep hidden |
|---|---|
| **B-TC14** | **Pending GCI, YTD closings, pipeline $** as File Desk headline KPIs. Money can exist later as a secondary tile; it must not lead a coordinator home. |
| **B-TC15** | **Representation** — already hidden; keep hidden. |
| **B-TC16** | **Task / Vendor template admin and Team Playbook** — already hidden; keep hidden. Do not “give TC the Team Lead libraries so they match Agent owner.” |
| **B-TC17** | **Invite to team** on File Desk — that is Team Lead. Owner **Users & Invites** is a different job (hire into the tenant) and belongs on owner chrome, not as a fake Team Lead CTA. |
| **B-TC18** | Brand **Team Command** for any TC with `team_id`. |
| **B-TC19** | Agent-identical Ask AI hint and Agent dashboard API as the File Desk source of truth. |

Correctly **absent** (keep absent): Team sidebar, Admin Oversight, AI Governance, Advertising, fake AI Coach.

---

## 5. Shared staff-shell problems that hit both desks differently

These are not “make them like Agent.” They are one `AppLayout` still differentiating mostly by hiding sections.

| Issue | Team Lead impact | TC impact |
|---|---|---|
| Intelligence group below the 768 fold | Worse: Team group pushes AI Suggestions to ~y 888 | Intelligence starts ~y 795 |
| No sidebar Settings item | Owner + identity setup only via avatar | Same |
| `showAiBriefingBar: true` on the default internal shell | Team Command gets the Agent-style briefing bar | File Desk gets it too |
| Documents / Task Queue unlabeled for identity | “My” queue on a team desk | Agent queue on a file desk |

Fake Coach Pro on Analytics did **not** reproduce for either founder (`ui.s8.analytics_coach_pro` ABSENT). Empty-queue “prospect” copy did **not** reproduce. Do not spend time on those.

---

## 6. Priority (what to fix first)

**P0 — Owner independence on these two homes (Layer A)**  
A1–A4: Billing, Change my role, and tenant invites reachable from Team Command and File Desk without Admin identity (avatar and/or home chip is enough; a second sidebar taxonomy is not required).  
A5 / B-TL6 / B-TC5: stop telling owners to switch to Admin.

**P1 — Stop identity theft (Layer B)**  
B-TL1 / B-TL16: Team Command is Team Lead-only; teamed Agents keep an Agent workspace with team scope.  
B-TC1 / B-TC7: File Desk is not `SoloAgentDashboardPage`.  
B-TC2 / B-TC18: TC brand is never Team Command.

**P2 — Role features that are missing or in the wrong place**  
Team Lead: B-TL2, B-TL3, B-TL5, B-TL12–B-TL14 (Team nav visible; invite stays on the team; playbook/automation from Team Command; communication audit as TL nav).  
TC: B-TC8–B-TC11, B-TC13 (intake CTA, complete-file checklist, vendor defaults, queue-first nav/KPIs).  
Both: B-TL8 / B-TL19 leftover Coach language; B-TL9 stub contact actions.

**P3 — Cleanup**  
B-TL4 / B-TL17 duplicate team pages; B-TL18 dead `TeamRailFeeds`; B-TC6 owner read of task templates; Documents/Task Queue copy.

---

## 7. What this review is not asking for

- Identical chrome, KPIs, or CTAs across Agent, Team Lead, and TC.
- Auto-promoting a Team Lead or TC founder to Admin so they can “finish setup.”
- Giving TC Team Lead libraries, Team Command, or Invite to team.
- Giving Team Lead Advertising, Payment Access, AI Governance, Audit Log, or Admin Console.
- Reintroducing seat caps or “credits” in customer copy.
- Treating Settings-hub owner cards as a substitute for **on-workspace** owner jobs (the cards can stay; they cannot be the only path).

A person who creates a **Team Lead** account is a Team Lead: they run Team Command, set the team playbook, invite into that team, and — because they own the tenant — they also pay and can change identity, from that same workspace. A person who creates a **Transaction Coordinator** account is a coordinator: they run File Desk, intake and chase the file, and — because they own the tenant — they also pay and hire, without becoming an Agent or an Admin. Those two sentences are the bar this review used.
