# Velvet Elves Revenue Generation System Plan

**Last updated:** 2026-06-08 (source-verification corrections added; see Section 1.5)  
**Audience:** Jan, the solo developer building Velvet Elves, and Jake, the client/product stakeholder.  
**Context:** This rewrite incorporates Jake's testing notes about signup roles, organization structure, vendor organizations, partner codes, Transaction Coordinators as vendor-style service providers, and post-MVP monetization paths.

---

## 1. Executive Summary

Velvet Elves should generate revenue as a real-estate workflow platform with several coordinated money streams:

1. **Core SaaS subscriptions** paid by the organization that owns the workspace.
2. **Paid internal staff seats** for Admins, Team Leaders, Agents, Attorneys, and any staff-style internal roles that remain.
3. **Vendor organization plans** for mortgage companies, title companies, TC companies, and other service providers that want multiple vendor users under one organization.
4. **Vendor-funded partner codes** that let a vendor organization subsidize all or part of an agent/team/attorney/FSBO transaction fee when that vendor is attached to the transaction.
5. **Workflow payments** that let tenants invoice and collect money from external parties through the existing Stripe payment rails.
6. **Paid add-ons** such as AI Coach Pro, advanced analytics, AI usage packs, white-label/custom domain, and concierge setup.
7. **Advertising packages** for clearly labeled sponsored placements, separate from vendor partner-code monetization.
8. **Services revenue** from onboarding, template configuration, migration, training, and enterprise rollout.

The new client feedback changes the revenue plan in one meaningful way: **vendor organizations are no longer just portal users inside a brokerage.** Mortgage vendors, title vendors, and Transaction Coordinator companies should eventually be able to exist as their own organizations with their own users, their own limits, their own codes, and their own billing responsibilities.

That does not need to be MVP, but the foundation should be shaped now so Jan does not paint the system into a corner.

The key product principle:

> A person can be the owner/Admin of their own workspace while also having a separate market-facing account type such as Agent, Team Leader, Attorney, FSBO, Mortgage Vendor, Title Vendor, or Transaction Coordinator.

This solves Jake's signup concern without weakening the owner/admin safety guardrails. The product can let a new self-signup choose and later correct their **account type** while keeping workspace ownership protected.

---

## 1.5 Source-Verification Corrections (2026-06-08)

This section was added after re-reviewing the plan against the live frontend and backend source, the requirements, and the shipped migrations. It is **authoritative**: where the body of this plan (Sections 2 onward) conflicts with a correction below, the correction wins. Each item names the file that was verified so the plan stops drifting from the code.

### C1. The phone-masking bug is already fixed (remove from the build queue)

The plan says (Section 2.1, Section 5.4, Section 10 Phase 0, Section 13) that phone masking adds a leading `1` and drops the final digit, and lists fixing it as immediate work. **This is stale.** `toNationalPhoneDigits` in `velvet-elves-frontend/src/utils/formatters.ts` already strips a leading country-code `1` from an 11-digit input *before* capping at 10 digits, with a comment describing exactly this bug. `formatPhoneNumber` (same file) and `RegisterPage.tsx` already use it.

- **Correction:** Do not schedule this as new work. Convert it to a one-line regression test (paste `+1 (317) 555-1234`, confirm `(317) 555-1234` with no lost digit). If a tester still saw the old behavior, they were on a stale build; reproduce on `main` before filing.

### C2. Company/Brokerage carry-over: fix the exact field mapping, not a vague pre-fill

The carry-over gap is real but the plan's description is imprecise. At registration, `RegisterPage.tsx` sends `organization_name`, which seeds the **tenant** display name (`tenants.name`). The onboarding company field in `OnboardingWizard.tsx` initializes its `companyName` state from `user?.company_name` (lines ~191 and ~255), **not** from the tenant name, so a fresh self-signup sees a blank company field even though they typed an organization at signup.

- **Correction:** The fix is specifically to seed the onboarding company field from `tenant.name` (already fetched via `useCurrentTenant` in the wizard) when `user.company_name` is empty: `companyName = user?.company_name || tenant?.name || ''`. Do not invent a new carry-over channel; the value already exists on the tenant.

### C3. Do not create `transaction_vendor_links` — extend the shipped `transaction_vendor_assignments`

This is the most important correction. The plan (Section 3.4, Section 7.2, Section 7.4, Section 9.5, Section 12.2, Section 13) proposes a new first-class table `transaction_vendor_links`. **That table already exists under a different name.** Milestone 4.3 shipped `public.transaction_vendor_assignments` (migration `20260622090000_milestone_4_3_vendor_comms.sql`): `id, tenant_id, transaction_id, vendor_id, role, notes, is_active, created_by, created_at, updated_at, UNIQUE(transaction_id, vendor_id, role)`, plus a companion `transaction_vendor_assignment_contacts` for the per-transaction primary/opt-in contact (the "vendor user" the plan wants). Repositories, API routes, and the wizard already read and write it.

Creating a parallel `transaction_vendor_links` would split "which vendor is on this deal" across two tables and produce two sources of truth, which is exactly the workflow break this review exists to prevent.

- **Correction:** Add the monetization fields to `transaction_vendor_assignments` rather than create a new table. New columns to add when Phase 4/5 lands: `partner_code_id`, `agreement_id`, `vendor_user_id` (or reuse the assignment-contact as the vendor user), `link_source`, `linked_by_user_id` (intent rename of `created_by`), `fee_split_snapshot_json`, `compliance_snapshot_json`. Everywhere the plan says "transaction vendor links," read it as "extend `transaction_vendor_assignments`." Also note `user_preferred_vendors` (migration `20260802090000_milestone_5_3_personalization.sql`) already exists and should feed the AI Coach relationship reporting in Section 6.7 rather than being rebuilt.

### C4. New plan keys require migrating the existing CHECK constraint

The plan introduces a `Brokerage` plan and a `Vendor Organization` plan (Section 6.1) and lists `plan_key` values "Trial, Solo, Team, Brokerage, Vendor, Enterprise" (Section 8.3). But the live column constraint, set in `20260512094000_tenant_plan_seats_and_grandfather.sql`, is `CHECK (plan IN ('trial','solo','team','enterprise'))`. Inserting a `brokerage` or `vendor` plan today would be rejected at the database.

- **Correction:** Any phase that introduces new plan tiers must include a migration that drops and re-adds `tenants_plan_check` with the expanded value set, and the Section 6.1 plan names must be reconciled with the lowercase keys the column actually stores. Until then, "Brokerage" maps to the existing `team`/`enterprise` tiers and is a pricing label, not a new DB value.

### C5. Vendor organizations and partner codes need a cross-tenant model that does not exist yet

Today a vendor is a **tenant-scoped row** in `public.vendors` (migration `202603110000_new_vendors_and_ad_hooks.sql`), and the entire M4.3 vendor system, plus RLS, is strictly tenant-scoped (every table carries `tenant_id`, policies are service-role). The plan's vision of a `vendor_organization` as its **own tenant** that issues partner codes to **other** tenants (Section 4.3, 6.4), and the "TC starts the transaction and selects the Agent" flow that writes into the agent's tenant (Section 4.4, 9.5), both require cross-tenant linkage and membership that the current architecture does not support and that tenant isolation actively prevents.

- **Correction:** Keep these explicitly behind the post-MVP cross-organization foundation (the plan already defers the join/merge flow in Section 10 Phase 7; partner codes and vendor-org-as-tenant belong on that same dependency). The MVP/near-term foundation (account_type, organization_type, vendor_category) is safe to add now because it does not cross tenants. Add one line to Phases 3 to 5 acceptance: "no cross-tenant read or write is introduced; vendor-org-to-other-tenant linkage waits for the Phase 7 cross-org model." Also flag in Section 11.2 that partner-code attribution spanning tenants is a tenant-isolation change requiring its own security review.

### C6. Confirmed-accurate claims (no change needed)

For the record, these plan claims were checked and are correct: the `UserRole` enum values (Section 5.1) match `app/models/enums.py` exactly; self-registration does default the registrant to Admin/owner and exposes no role picker (`RegisterPage.tsx` confirms, by design); `account_type`, `organization_type`, `vendor_category`, and `company_display_name` do not exist yet, so adding them is genuinely new; the seat model already excludes Client/ForSaleByOwner/Vendor portal accounts (`20260512094000`), so the billable-vs-portal split in Section 6.2 is consistent with the code; and all three migrations cited in Section 16 exist. One minor internal inconsistency: `transaction_fee_splits` is listed in both Section 7.2 and Section 7.5; keep it only under the sponsored-fee tables (7.5).

---

## 2. What The Testing Notes Changed

### 2.1 Signup and onboarding feedback

Jake observed:

- A new public signup defaults to Admin.
- The user cannot pick a visible account type at signup.
- The user cannot change role/account type on Step 2.
- Company/Brokerage entered at signup did not carry into Step 2.
- Phone masking added a leading `1` and dropped the final digit. **[Corrected 2026-06-08 — already fixed in source (`toNationalPhoneDigits`, `src/utils/formatters.ts`); see Section 1.5 C1. Treat as a regression test, not new work.]**
- Vendor/client roles created from a transaction should remain system-assigned and locked.

Jan's explanation remains correct:

- Today every public signup creates a new private workspace.
- The first user becomes owner/Admin so they cannot be locked out.
- Invited users and transaction-created portal users should not self-change their role.

The plan update:

- Keep owner/Admin permission protection.
- Add a separate **self-selected account type** at signup.
- Let a self-signup correct that account type on Step 2.
- Do not let an invited or transaction-created user self-change the role assigned by the system.
- Fix the phone masking and company carry-over bugs.

### 2.2 Vendor monetization feedback

Jake's model:

- A vendor company can offer Velvet Elves as a perk to do business with that vendor organization.
- A vendor organization can contain multiple individual vendor users, such as several loan officers or title reps.
- A vendor organization can issue a unique code to an Agent, Team Leader, TC, FSBO, Attorney, brokerage, or team.
- The agent or organization can hold multiple active codes from multiple vendors of the same type.
- When a transaction is started, the transaction checks whether a linked vendor organization is attached.
- If linked, the vendor pays its agreed percentage or share.
- If not linked, the agent or owner organization covers the full fee.
- The vendor organization must actually be attached to the transaction to owe anything.
- Each vendor organization controls its own codes, limits, budgets, revocations, and sales rules.
- The system needs compliance proof: written agreement, code linkage, transaction linkage, and audit trail.

This makes sense and should become a post-MVP revenue expansion path.

### 2.3 TC role feedback

Jake's updated direction:

- Transaction Coordinators should generally be treated more like a vendor/service-provider category than an internal staff role.
- In the wizard, an Agent, FSBO, Attorney, Team Leader, or Admin should be able to add a TC the same way they add a title or mortgage vendor.
- A TC company can have multiple individual TCs.
- An in-house TC company can be selected by choosing the company and drilling down to a specific TC.
- A third-party TC company works the same way.
- If the TC starts the transaction, the TC uses the wizard and selects the Agent, instead of the Agent selecting the TC.

The plan update:

- Keep the existing `TransactionCoordinator` staff role for backward compatibility and possible in-house staff workflows.
- New monetization and vendor-org architecture should model TC companies as `Vendor Organization + category=transaction_coordination`.
- Do not force TC vendors to consume brokerage paid staff seats when they are operating as outside service providers.

### 2.4 Organization and team feedback

Jake and Jan aligned on:

- A Team is not its own organization.
- A Team is a sub-group inside one organization.
- A brokerage can have multiple teams and standalone agents.
- Team creation is manual and Admin-triggered.
- Mortgage and title vendors should also be able to form their own organizations later.
- A person who created their own workspace first cannot currently join another brokerage with the same account.
- That "join an existing brokerage after self-signup" flow is post-MVP.
- If that post-MVP flow is built, the original data and transactions should stay with the person's original account/workspace.

The plan update:

- Do not turn teams into organizations.
- Add organization types instead: agent workspace, brokerage workspace, vendor organization, attorney practice, FSBO workspace, and platform.
- Post-MVP, add controlled cross-organization membership or migration flows.

---

## 3. Revenue Principles

### 3.1 Keep billing understandable

There are now four different money concepts. They must stay separate:

1. **Velvet Elves SaaS subscription revenue**
   - The platform charges a workspace for access, seats, and add-ons.

2. **Tenant workflow payments**
   - A tenant uses Velvet Elves to collect an invoice from a client or counterparty.
   - This is not automatically Velvet Elves revenue.

3. **Vendor-funded sponsorship or subsidy**
   - A vendor organization pays a share of a specific transaction fee because its code and organization were attached to that transaction.

4. **Advertising purchases**
   - An advertiser buys a sponsored placement package.
   - This is not the same as vendor-funded transaction sponsorship.

### 3.2 Keep external transaction participants free by default

The product should not punish the workflow for collaboration.

Non-billable portal users should remain free:

- Client
- FSBO participant when transaction-scoped
- Vendor user attached to a transaction
- Buyer/seller contact
- External service contact

Billable users should be internal staff or organization members who operate the workspace:

- Admin
- Team Leader
- Agent
- Attorney, when acting as an internal workspace user
- Internal staff TC, if that model remains for a tenant
- Vendor organization staff, when the vendor organization itself has a paid vendor plan

### 3.3 Protect trust before extracting fees

Vendor sponsorship is sensitive. The system should never make it look like the AI or workflow is recommending a vendor because that vendor paid.

Rules:

- The vendor has to be attached to the transaction before the fee split applies.
- Sponsorship must be explicit and auditable.
- Sponsored ads must be clearly labeled.
- AI recommendations must not hide commercial incentives.
- Any referral or settlement-service compensation model needs legal/compliance review.

### 3.4 Build for post-MVP without overbuilding MVP

The vendor organization and partner-code model does not have to ship in MVP. But the data model should avoid assumptions that make it expensive later.

Do now:

- Separate account type from permission role.
- Preserve organization type as a first-class concept.
- Keep vendors category-driven.
- Design transaction vendor links as first-class, auditable records.
- Keep billing per organization.

Do later:

- Vendor organization self-service.
- Partner code issuance.
- Fee split automation.
- Vendor ROI reports.
- AI Coach relationship monitoring.
- Existing-account join/merge workflows.

---

## 4. Updated Organization Model

### 4.1 Organization types

Today the system treats a new self-signup as an owner of a new organization. Keep that pattern, but make the organization's market type explicit.

Recommended organization types:

| Organization type | Description | MVP? |
| --- | --- | --- |
| `solo_agent_workspace` | One agent's private workspace. | Yes |
| `team_or_brokerage_workspace` | Brokerage or team workspace with internal staff, teams, and shared templates. | Yes |
| `attorney_practice` | Attorney-owned workspace for legal/matter work. | Maybe, if attorney workspace is included. |
| `fsbo_workspace` | FSBO-owned direct workspace. | Existing FSBO product path; billing TBD. |
| `vendor_organization` | Mortgage, title, TC, inspection, home warranty, or other service provider organization. | Post-MVP foundation, not full launch. |
| `platform` | Velvet Elves internal operations. | Yes |

### 4.2 Team is not an organization

A Team remains a sub-group inside one organization.

Example:

```text
Acme Realty Organization
  - Admin: Jane
  - Team: North Side Team
    - Team Leader: Sam
    - Agents: A, B, C
  - Team: Luxury Team
    - Team Leader: Priya
    - Agents: D, E
  - Standalone Agents: F, G
```

All teams share:

- One tenant.
- One bill.
- One Admin layer.
- One data boundary.
- One subscription state.

### 4.3 Vendor organization is an organization

A vendor organization is not just a single contact inside an agent's workspace.

Example:

```text
Chicago Title Organization
  - Vendor Admin: Regional manager
  - Vendor Users:
    - Title rep 1
    - Title rep 2
    - Escrow contact
  - Partner Codes:
    - CHI-TITLE-SAM
    - CHI-TITLE-NORTHSIDE
  - Agreements:
    - Agreement with Sam Agent
    - Agreement with North Side Team
  - Limits:
    - Monthly sponsorship budget
    - Max transactions per code
    - Active date range
```

The same pattern works for:

- Mortgage companies.
- Title companies.
- Transaction coordination companies.
- Inspection companies.
- Home warranty companies.
- Any other vendor category approved later.

### 4.4 TC organization as vendor organization

Transaction Coordination should be modeled as a vendor category for the new workflow:

```text
Vendor Organization
  category = transaction_coordination
  users = individual TCs
```

Two flows:

1. **Agent starts the transaction**
   - Agent selects TC company in the wizard.
   - Agent selects or invites a specific TC.
   - TC receives welcome/invite email.
   - Transaction link records TC company, TC user, and any partner code.

2. **TC starts the transaction**
   - TC starts the wizard from the TC/vendor workspace.
   - TC selects the Agent and agent organization.
   - Transaction is created with Agent as owner or required participant.
   - TC company is attached as the TC vendor organization.

Backward compatibility:

- Existing `TransactionCoordinator` staff role should not be deleted abruptly.
- For in-house staff TCs, the current staff model can keep working.
- For the global product model and new monetization, TC should be treated as vendor organization + vendor user.

---

## 5. Signup, Account Type, And Role Model

### 5.1 Separate "permission role" from "account type"

This is the cleanest way to satisfy Jake's signup request without breaking workspace ownership.

| Concept | Purpose | Example values |
| --- | --- | --- |
| Permission role | Controls what the user can do in a workspace. | Admin, TeamLead, Agent, Attorney, Vendor, Client, ForSaleByOwner |
| Account type | Describes how the user identifies commercially. | Agent, Team Leader, Attorney, FSBO, Mortgage Vendor, Title Vendor, Transaction Coordinator |
| Organization type | Describes what kind of workspace the tenant is. | solo_agent_workspace, vendor_organization, attorney_practice |
| Vendor category | Describes service-provider type. | mortgage, title, transaction_coordination, inspection |

Self-signup example:

```text
User picks: Team Leader
System creates: new organization
Permission role: Admin/Owner
Account type: Team Leader
Organization type: team_or_brokerage_workspace
```

Vendor signup example:

```text
User picks: Mortgage Vendor
System creates: vendor organization
Permission role: Admin/Owner
Account type: Mortgage Vendor
Organization type: vendor_organization
Vendor category: mortgage
```

This means the UI can stop showing a confusing "Admin" answer where Jake expects "Agent" or "Team Leader." Internally, the user is still protected as the workspace owner.

### 5.2 Signup dropdown

Public signup should offer:

- Agent
- Team Leader
- Attorney
- For Sale by Owner
- Transaction Coordinator
- Mortgage Vendor
- Title Vendor

Brokerage/Broker should remain manually set up later, per Jake's note.

Recommended mapping:

| Signup choice | Permission role on own workspace | Account type | Organization type | Notes |
| --- | --- | --- | --- | --- |
| Agent | Admin/Owner | Agent | solo_agent_workspace | Can later invite or join brokerage post-MVP. |
| Team Leader | Admin/Owner | Team Leader | team_or_brokerage_workspace | Does not automatically create a team unless we add a prompt. |
| Attorney | Admin/Owner | Attorney | attorney_practice | Attorney workspace rules still apply. |
| For Sale by Owner | Admin/Owner or FSBO Owner | FSBO | fsbo_workspace | Direct FSBO pricing can be decided later. |
| Transaction Coordinator | Admin/Owner | Transaction Coordinator | vendor_organization | Category `transaction_coordination`. |
| Mortgage Vendor | Admin/Owner | Mortgage Vendor | vendor_organization | Category `mortgage`. |
| Title Vendor | Admin/Owner | Title Vendor | vendor_organization | Category `title`. |

### 5.3 Step 2 role/account correction

Step 2 should let a self-signup correct their account type.

Rules:

- If the user created their own workspace, account type is editable on Step 2.
- Changing account type updates `account_type` and, when relevant, organization type/category.
- The owner/admin permission is not removed automatically.
- If the user came from an invitation, Step 2 does not allow self-changing the assigned role.
- If the user was created by being added to a transaction, Step 2 does not allow self-changing the assigned role.

This matches Jake's "people are stupid and maybe they didn't change it" note while preserving Jan's lockout protection.

### 5.4 Immediate onboarding fixes

These are not monetization features, but they affect revenue because signup friction affects conversion.

| Fix | Required behavior |
| --- | --- |
| Phone mask | **Already fixed in source (Section 1.5 C1).** Keep only a regression test: a leading US country code `1` is stripped before the 10-digit mask and no digit is dropped. |
| Company/Brokerage carry-over | Pre-fill Step 2 Company/Brokerage from the signup organization name. |
| Account type dropdown | Add public signup choice and store it. |
| Step 2 account correction | Let self-signups correct account type without demoting owner/admin. |
| Invited/transaction-created role lock | Keep locked. Role was assigned by inviter/system and should not be self-edited. |

---

## 6. Revenue Streams

### 6.1 Core SaaS subscriptions

The primary revenue stream should remain recurring SaaS subscriptions.

Candidate launch packaging:

| Plan | Target customer | Candidate price test | Included shape |
| --- | --- | --- | --- |
| Trial | New self-signup | Free for 14 days | Full core workflow, limited seats, limited AI allowance. |
| Solo | Solo Agent, Attorney, or solo TC workspace | `$99/month` or `$999/year` | 1 owner seat, core workflow, documents, tasks, client portal, email integrations. |
| Team | Team Leader or small TC/team operation | `$299/month` base including 3 seats, then `$59/seat/month` | Team dashboard, shared templates, staff invites, payment features. |
| Brokerage | Larger operations group | `$899/month` base including 10 seats, then negotiated per-seat | Admin controls, multi-team oversight, payment governance, advanced reporting. |
| Vendor Organization | Mortgage/title/TC company | `$199-$499/month` depending features | Multi-user vendor org, code issuance, partner management, sponsorship reporting. |
| Enterprise / White-label | Brokerage, franchise, strategic partner | Custom annual contract | Custom domain, white-label, migration, support, custom limits. |

Notes:

- Exact pricing needs Jake approval and market validation.
- Annual plans should offer a discount.
- Existing customers should remain grandfathered until a migration plan is approved.
- Vendor organization pricing should not be confused with sponsored transaction fees. A vendor may pay both a vendor-org subscription and transaction subsidies.

### 6.2 Paid internal seats

Billing should count internal staff seats, not every person attached to a transaction.

Billable staff examples:

- Admin
- Team Leader
- Agent
- Attorney, when operating inside an internal workspace
- Internal Transaction Coordinator, if using legacy staff TC model

Non-billable portal/service examples:

- Client
- FSBO participant on another party's deal
- Vendor contact attached to a transaction
- TC attached as vendor/service provider
- Title rep
- Mortgage loan officer

The important distinction:

> If the person is operating the workspace, they are probably a paid seat. If the person is participating in a transaction as an external party, they should usually be free or billed through their own vendor organization.

### 6.3 Vendor organization subscriptions

Vendor organizations should become a real paid customer segment post-MVP.

Vendor orgs pay for:

- Multiple users under one vendor company.
- Vendor profile and category management.
- Partner code issuance.
- Agreement storage.
- Budget/limit management.
- Transaction attribution.
- Performance reporting.
- AI Coach-style relationship insights later.

Candidate vendor plans:

| Vendor plan | Target | Candidate price test | Included shape |
| --- | --- | --- | --- |
| Vendor Basic | Small vendor shop | `$199/month` | Organization profile, up to 3 vendor users, limited active codes. |
| Vendor Growth | Regional title/mortgage/TC company | `$499/month` | More users, more codes, relationship reporting, higher sponsorship limits. |
| Vendor Enterprise | Large partner | Custom | Multi-branch reporting, custom agreements, API/export, dedicated support. |

### 6.4 Vendor-funded partner codes

This is Jake's new monetization model.

Plain-English model:

- Vendor organization creates a code.
- Vendor gives the code to an Agent, Team Leader, Attorney, FSBO, brokerage, or team.
- The recipient can hold multiple active codes from multiple vendors.
- The code can be attached to a transaction only when the vendor organization is attached to that transaction.
- If attached, the vendor pays the agreed share.
- If not attached, the agent or owning organization pays the full fee.
- The vendor can revoke or limit the code going forward.
- Revocation does not rewrite historical transaction obligations.

Example:

```text
Agent has codes:
  - CHICAGO-TITLE-25
  - FIRSTAM-TITLE-40
  - ROCKET-MTG-20
  - MERIDIAN-TC-50

New transaction:
  - Agent selects Chicago Title as title vendor
  - Agent selects Rocket Mortgage as lender vendor
  - System sees active codes for both organizations
  - Fee split is calculated from the transaction links
  - Chicago Title pays title-related agreed share
  - Rocket Mortgage pays lender-related agreed share
  - Any unsponsored portion remains with agent/agent organization
```

### 6.5 Sponsored transaction fee

The vendor code model implies some kind of transaction-level fee or credit.

Recommended foundation:

- Keep base SaaS subscriptions as the primary access revenue.
- Add a post-MVP **transaction platform fee** or **transaction credit model** that can be split by vendor sponsorship.
- Do not mix this directly into the existing tenant invoice/payment module until policy is approved.

Candidate models:

| Model | Description | Recommendation |
| --- | --- | --- |
| Subscription only | Vendor code gives discount on monthly subscription. | Easy but does not match "vendor must be attached to transaction" as cleanly. |
| Per-transaction platform fee | Every started transaction has a fee; linked vendor can pay a share. | Best match for Jake's model. |
| Transaction credit | Vendor prepays credits that apply only when attached to the transaction. | Good for budgets and limits. |
| Hybrid | Subscription for access, transaction fee for sponsored monetization. | Recommended long-term. |

Example fee split:

```text
Transaction platform fee: $50
Linked title vendor pays: 40% = $20
Linked mortgage vendor pays: 20% = $10
Agent/owner org pays remaining: $20
```

This is only an example. Jake should approve final economics.

### 6.6 Workflow payments

The existing payment module lets tenants collect money from external parties.

Examples:

- Transaction coordination fee.
- Compliance fee.
- Document preparation fee where allowed.
- Administrative fee.
- Commission-related payout tracking.

Default policy:

- This money belongs to the tenant.
- Velvet Elves should not take a platform fee at first.
- If a platform fee is added later, it must be transparent, auditable, refund-aware, and approved in terms/compliance copy.

Do not collect earnest money through Stripe. Earnest money is escrow-regulated and should remain outside Velvet Elves payment collection.

### 6.7 AI Coach Pro and relationship reporting

AI Coach Pro is already documented as a future paid add-on.

Jake's vendor-code model gives AI Coach a useful future role:

- Monitor how many transactions a vendor receives from each Agent, Team, or Brokerage.
- Show vendor conversion and usage reports.
- Identify stale partner codes.
- Recommend code renewal, revocation, or follow-up.
- Help agents understand which vendor relationships are active.
- Help vendor organizations decide whether a code is worth keeping.

This should be a paid reporting/add-on capability, not a hidden automated decision system.

AI Coach should recommend. The vendor organization should decide.

### 6.8 Advertising packages

Advertising remains a separate revenue stream.

Advertising package examples:

| Package | Buyer | Candidate price test |
| --- | --- | --- |
| Starter Sponsored Run | Local vendor/service provider | `$199` for 30 days |
| Premium Sponsored Run | Regional vendor/lender/title partner | `$499` for 30 days |
| Enterprise Sponsorship | Strategic partner | Custom |

Rules:

- Ads are opt-in by tenant.
- Ads are labeled `SPONSORED`.
- Ads do not imitate AI or system recommendations.
- Advertising does not prove a vendor relationship for transaction fee split.
- Vendor partner-code sponsorship is transaction-linked and agreement-backed; ads are marketing placements.

### 6.9 Services revenue

Services should be a real line item:

| Service | Candidate price test |
| --- | --- |
| Solo onboarding | `$250-$500` |
| Team setup | `$1,000-$2,500` |
| Brokerage migration | `$5,000+` |
| Vendor organization setup | `$500-$2,000` |
| Partner code program setup | `$1,000-$3,000` |
| Custom task templates | `$750-$3,000` |
| Training | `$500-$2,000` |
| Enterprise launch package | Custom |

For Jan as a solo developer, charging for setup protects development time and funds careful configuration instead of rushed custom work.

---

## 7. Required Data Model

### 7.1 Account and organization fields

Add or formalize:

| Field | Purpose |
| --- | --- |
| `tenants.organization_type` | Distinguish agent, brokerage, vendor org, attorney, FSBO, platform. |
| `users.account_type` | User's self-selected market identity. |
| `users.account_type_locked_reason` | Null for self-signup; set for invited/transaction-created users. |
| `tenants.vendor_category` | For vendor organizations: mortgage, title, transaction_coordination, etc. |
| `tenants.company_display_name` | User-visible company/brokerage/vendor name. |

Potential account type values:

```text
agent
team_leader
attorney
for_sale_by_owner
transaction_coordinator
mortgage_vendor
title_vendor
```

Potential organization type values:

```text
solo_agent_workspace
team_or_brokerage_workspace
attorney_practice
fsbo_workspace
vendor_organization
platform
```

Potential vendor categories:

```text
mortgage
title
transaction_coordination
inspection
home_warranty
attorney
other
```

### 7.2 Vendor organization tables

Proposed tables:

| Table | Purpose |
| --- | --- |
| `vendor_organization_profiles` | Vendor-specific profile for a tenant with `organization_type=vendor_organization`. |
| `vendor_service_categories` | Categories and service types supported by a vendor organization. |
| `vendor_org_memberships` | Vendor users inside a vendor organization, if the existing user table cannot represent this cleanly. |
| `vendor_partner_agreements` | Written agreement between vendor organization and agent/team/brokerage/FSBO/attorney recipient. |
| `vendor_partner_codes` | Vendor-owned codes with status, limits, budget, share, start/end date, and agreement ID. |
| `vendor_code_assignments` | Which person/team/brokerage has access to which vendor code. |
| `transaction_vendor_assignments` (extend; do **not** create `transaction_vendor_links`) | **[Corrected 2026-06-08 — Section 1.5 C3.]** This first-class transaction-to-vendor link already exists from M4.3 (`20260622090000`). Add monetization columns to it (vendor user via the existing assignment-contact, category, partner code, agreement, snapshots) instead of creating a parallel table. |
| `transaction_fee_splits` | Calculated sponsor obligations for a transaction. |
| `vendor_code_audit_events` | Code issued, accepted, used, revoked, expired, limit changed. |

### 7.3 Partner code fields

`vendor_partner_codes` should support:

| Field | Purpose |
| --- | --- |
| `vendor_tenant_id` | Vendor organization that owns the code. |
| `code` | Human-friendly unique code. |
| `vendor_category` | Mortgage, title, TC, etc. |
| `agreement_id` | Written agreement backing the code. |
| `status` | Draft, active, paused, revoked, expired. |
| `recipient_scope` | User, team, brokerage, attorney practice, FSBO workspace. |
| `recipient_id` | Specific recipient when assigned. |
| `sponsor_share_percent` | Percent of transaction fee vendor pays. |
| `sponsor_flat_cents` | Optional flat contribution. |
| `max_per_transaction_cents` | Cap per transaction. |
| `monthly_budget_cents` | Vendor monthly cap. |
| `lifetime_budget_cents` | Vendor lifetime cap. |
| `max_transactions` | Count limit. |
| `starts_at` / `ends_at` | Effective dates. |
| `requires_vendor_attached` | Should be true for Jake's model. |
| `metadata_json` | Sales notes, market, territory, internal tags. |

### 7.4 Transaction vendor link fields

The shipped `transaction_vendor_assignments` table (extended per Section 1.5 C3, not a new `transaction_vendor_links` table) should gain support for:

| Field | Purpose |
| --- | --- |
| `transaction_id` | Deal being linked. |
| `vendor_tenant_id` | Vendor organization. |
| `vendor_user_id` | Individual loan officer, title rep, or TC when selected. |
| `vendor_category` | Mortgage, title, TC, etc. |
| `partner_code_id` | Code used, if any. |
| `agreement_id` | Agreement backing the relationship. |
| `link_source` | Wizard, admin edit, vendor-started transaction, API, migration. |
| `linked_by_user_id` | Who attached the vendor. |
| `linked_at` | Timestamp. |
| `fee_split_snapshot_json` | Immutable snapshot of split terms at link time. |
| `compliance_snapshot_json` | Agreement/code proof at link time. |
| `status` | Active, removed, replaced. |

Important:

- If a code is revoked later, old transactions keep their snapshot.
- If a vendor is removed from a transaction, future fee obligations should stop according to policy.
- Historical audit should remain intact.

### 7.5 Billing tables

For SaaS and vendor organization billing:

| Table | Purpose |
| --- | --- |
| `billing_customers` | Stripe customer per organization. |
| `billing_subscriptions` | Stripe subscription mirror. |
| `billing_subscription_items` | Plan, seat, and add-on items. |
| `billing_entitlements` | Current computed capabilities. |
| `billing_usage_events` | AI and usage metering. |
| `billing_invoices` | Subscription invoice mirror. |
| `tenant_plan_overrides` | Grandfathering and enterprise exceptions. |

For sponsored transaction fee billing:

| Table | Purpose |
| --- | --- |
| `transaction_fee_events` | Fee generated by transaction creation or milestone. |
| `transaction_fee_splits` | Who owes what share. |
| `sponsor_obligations` | Vendor amounts due from partner code use. |
| `sponsor_invoices` | Vendor invoices or Stripe charges for sponsored amounts. |
| `sponsor_credits` | Prepaid vendor credits, if using a credit model. |

---

## 8. Billing Architecture

### 8.1 Stripe modes

| Use case | Stripe mode | Status |
| --- | --- | --- |
| Tenant invoice to external payer | Checkout `mode=payment` | Existing M5.2 pattern. |
| Advertising package purchase | Checkout `mode=payment` | Existing/planned M6.2 pattern. |
| SaaS plan subscription | Checkout `mode=subscription` | New. |
| Vendor organization subscription | Checkout `mode=subscription` | New. |
| Customer billing portal | Stripe Customer Portal | New. |
| Sponsored transaction fee | Invoice item, subscription usage, credit ledger, or separate payment | Post-MVP decision. |
| AI usage/overage | Metered price or internal ledger with monthly invoice item | New/post-MVP. |

### 8.2 Source of truth

The source of truth should be:

1. Stripe for active subscription status and payment collection.
2. Velvet Elves billing tables for entitlements, local reporting, code linkage, and compliance proof.
3. Platform overrides for pilots, legal holds, enterprise contracts, and grandfathering.

Do not treat `tenants.plan` alone as the complete billing source of truth once Stripe Billing is live. It should become a derived operational field.

### 8.3 Entitlements

Every paid feature should use a shared entitlement service.

Recommended endpoint:

```text
GET /api/v1/billing/entitlements
```

Entitlement examples:

| Entitlement | Purpose |
| --- | --- |
| `plan_key` | Trial, Solo, Team, Brokerage, Vendor, Enterprise. **[Corrected 2026-06-08 — the DB column today only allows `trial/solo/team/enterprise`; adding `brokerage`/`vendor` requires migrating `tenants_plan_check`. See Section 1.5 C4.]** |
| `staff_seat_limit` | Paid internal staff cap. |
| `vendor_user_limit` | Vendor org user cap. |
| `partner_code_limit` | Active code cap for vendor orgs. |
| `payments_enabled` | Tenant can create workflow invoices. |
| `team_templates_enabled` | Team-level templates available. |
| `vendor_partner_program_enabled` | Vendor can issue codes. |
| `sponsored_transaction_fee_enabled` | Transaction fee split feature enabled. |
| `ai_monthly_credit_limit` | Included AI allowance. |
| `ai_coach_enabled` | AI Coach feature gate. |
| `white_label_enabled` | Branding/custom domain features. |
| `billing_grace_state` | Active, past_due, grace, restricted, suspended. |

### 8.4 Fee-split calculation rule

The first implementation should be deterministic.

Suggested calculation:

```text
1. Transaction creates a fee event.
2. System checks transaction_vendor_links.
3. For each active vendor link:
   - Verify code is active.
   - Verify code belongs to linked vendor organization.
   - Verify code requires vendor attached, and vendor is attached.
   - Verify category matches.
   - Verify budget and transaction limits.
4. Calculate vendor share.
5. Apply caps.
6. Remaining balance goes to owning agent/team/brokerage organization.
7. Store immutable split snapshot.
8. Bill vendor and owner organization according to payment policy.
```

No vendor should be charged because an agent merely has a code in their account. The code must be used on a transaction with that vendor attached.

---

## 9. Customer-Facing Product Surfaces

### 9.1 Signup

Add public signup fields:

- Account type dropdown.
- Company/Brokerage/Vendor company name.
- For vendor account types, vendor category is inferred or selected.

Behavior:

- Self-signup creates a new workspace.
- Founder remains protected as owner/Admin.
- Account type is visible and editable during onboarding.
- Invited users follow assigned role.
- Transaction-created users follow assigned role.

### 9.2 Onboarding Step 2

Add:

- Account type selector for self-signups.
- Organization name pre-filled from signup.
- Phone field with corrected masking.
- Clear explanation that "Workspace owner" is protected.

Do not show "Admin" as the user's identity if Jake expects Agent/Team Leader/etc. Show:

```text
Account type: Agent
Workspace permission: Owner/Admin
```

Or hide the permission detail unless needed.

### 9.3 Billing page

Add Organization -> Billing or Settings -> Billing.

Sections:

- Current plan.
- Subscription status.
- Seats used.
- Vendor users used, for vendor organizations.
- Payment method via Stripe Customer Portal.
- Subscription invoices.
- Add-ons.
- AI usage.
- Partner code program status, for vendor organizations.

### 9.4 Vendor organization dashboard

For vendor organizations:

- Company profile.
- Vendor categories.
- Vendor users.
- Partner agreements.
- Partner codes.
- Active code assignments.
- Sponsored transaction obligations.
- Monthly budget usage.
- Transactions received by source agent/team/brokerage.
- Code revocation controls.
- AI Coach relationship insights later.

### 9.5 Transaction wizard updates

For Agent/Team/Admin/Attorney/FSBO started transactions:

- Add TC selection the same way title/mortgage vendors are selected.
- Allow vendor organization and vendor user drill-down.
- Show active partner codes for selected vendor organizations.
- Explain fee split only where appropriate and approved.
- Store transaction vendor links as first-class records.

For TC-started transactions:

- TC selects agent/agent organization.
- TC organization is attached as vendor category `transaction_coordination`.
- Agent remains owner or primary transaction party according to workflow rules.

### 9.6 Partner code management

Agent/team/brokerage side:

- List active vendor codes.
- Show vendor organization, category, status, expiry, and terms summary.
- Allow code redemption/acceptance.
- Show which transactions used which code.

Vendor side:

- Issue code.
- Assign to user/team/brokerage.
- Pause/revoke code.
- Set limits.
- View usage.
- Export compliance proof.

### 9.7 Platform revenue console

Platform -> Revenue should show:

- MRR / ARR.
- Trial funnel.
- Paid tenants.
- Vendor organization customers.
- Seat revenue.
- Add-on revenue.
- Sponsored transaction fee revenue.
- Vendor sponsor obligations.
- Ad revenue.
- Failed subscription payments.
- Workflow payment GMV, clearly labeled as tenant-collected volume.
- AI usage cost and margin.

---

## 10. Implementation Plan

### Phase 0 - Immediate onboarding fixes

Goal: remove testing friction and make signup language match Jake's expectations.

Work:

1. Fix phone masking: **[Corrected 2026-06-08 — already shipped in `toNationalPhoneDigits` (`src/utils/formatters.ts`); see Section 1.5 C1. Replace this item with a regression test only.]**
   - Strip leading `1` before 10-digit mask.
   - Preserve all real digits.

2. Fix Company/Brokerage carry-over:
   - Pre-fill Step 2 from organization/company name captured at signup.

3. Add account type dropdown at signup:
   - Agent
   - Team Leader
   - Attorney
   - For Sale by Owner
   - Transaction Coordinator
   - Mortgage Vendor
   - Title Vendor

4. Add account type field on onboarding Step 2:
   - Editable for self-signup.
   - Locked for invited and transaction-created users.

5. Keep owner/Admin protected:
   - Do not let a founder accidentally demote themselves.
   - If needed, show "Account type" rather than "Role" to avoid confusion.

Acceptance:

- A new user can choose Agent/Team Leader/etc. at signup.
- Step 2 shows the selected account type and lets self-signups correct it.
- Owner permission remains protected.
- Company/Brokerage value carries into Step 2.
- Phone number no longer loses the last digit.

### Phase 1 - Core SaaS billing foundation

Goal: answer the existing subscription gap.

Backend:

1. Add billing tables:
   - `billing_customers`
   - `billing_subscriptions`
   - `billing_subscription_items`
   - `billing_entitlements`
   - `billing_invoices`
   - `tenant_plan_overrides`

2. Add Stripe Billing service:
   - Create customer.
   - Create subscription Checkout Session.
   - Create Customer Portal Session.
   - Sync subscription state from webhooks.

3. Add subscription webhooks:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`

4. Compute entitlements:
   - Plan key.
   - Seat limit.
   - Billing state.
   - Feature flags.

Frontend:

1. Add `/pricing`.
2. Add Organization -> Billing.
3. Add upgrade path from seat-limit errors.
4. Add platform tenant billing state.

Acceptance:

- A self-signup can start trial and upgrade to a paid plan.
- Customer can open Stripe Customer Portal.
- Webhook replay does not duplicate state.
- Platform admin can see subscription status.

### Phase 2 - Organization type foundation

Goal: prepare for vendor organizations without launching the whole vendor monetization program.

Work:

1. Add `organization_type`.
2. Add `account_type`.
3. Add `vendor_category` for vendor orgs.
4. Update signup/onboarding to map choices into these fields.
5. Update platform tenant detail to show organization type and account type.
6. Preserve existing role/RBAC behavior.

Acceptance:

- Agent signup creates an agent-style workspace.
- Mortgage Vendor signup creates or can create a vendor organization shell.
- Title Vendor signup creates or can create a vendor organization shell.
- TC signup creates or can create a vendor organization shell with category `transaction_coordination`.
- No full partner-code program is required yet.

### Phase 3 - Vendor organization MVP shell

Goal: make vendor organizations real enough to build on.

Work:

1. Vendor organization profile page.
2. Vendor user management.
3. Vendor category management.
4. Vendor organization billing plan.
5. Basic vendor directory/search for transaction wizard.
6. TC vendor category in wizard.

Acceptance:

- A mortgage/title/TC organization can exist independently.
- It can have multiple users.
- It can be selected in a transaction.
- A transaction can store an auditable vendor organization link.

### Phase 4 - Partner codes and agreements

Goal: implement Jake's vendor code model.

Work:

1. Add `vendor_partner_agreements`.
2. Add `vendor_partner_codes`.
3. Add `vendor_code_assignments`.
4. Add vendor-side code creation/revocation UI.
5. Add agent/team/brokerage-side code acceptance/list UI.
6. Add transaction wizard code application.
7. Add immutable transaction link snapshot.
8. Add compliance/audit export.

Acceptance:

- Vendor organization can issue a code.
- Agent/team/brokerage can hold multiple codes from multiple vendors.
- A transaction can apply the correct code only when that vendor is attached.
- Vendor can revoke future code usage.
- Historical transactions keep proof.

### Phase 5 - Sponsored transaction fee split

Goal: turn partner codes into money movement.

Decisions needed first:

- What transaction fee is being split?
- Is the fee charged at transaction creation, milestone, closing, or monthly invoice?
- Does vendor pay immediately, from prepaid credit, or via monthly invoice?
- Are multiple vendor shares allowed on one transaction?
- What happens if vendor budget is exhausted?

Work:

1. Add transaction fee events.
2. Add fee split calculator.
3. Add vendor sponsor obligations.
4. Add owner organization remaining-balance obligation.
5. Add billing/invoicing for sponsor obligations.
6. Add refunds/voids/reversals policy.
7. Add reports.

Acceptance:

- If no vendor is linked, owner organization owes full transaction fee.
- If linked vendor with active code is attached, vendor owes agreed share.
- If multiple eligible vendors are attached, fee split follows configured priority/caps.
- Compliance proof is available.
- Vendor budgets and limits are enforced.

### Phase 6 - AI Coach relationship intelligence

Goal: monetize relationship monitoring after code usage exists.

Work:

1. Vendor ROI report:
   - Transactions received.
   - Agents sending deals.
   - Codes used.
   - Sponsored amount.
   - Revenue/relationship trend.

2. AI Coach recommendations:
   - Stale code.
   - High-performing partner.
   - Code nearing budget cap.
   - Agent with code but no transactions.
   - Vendor should follow up.

3. Human approval:
   - AI recommends.
   - Vendor decides whether to revoke, renew, or adjust.

Acceptance:

- Vendor organization can understand whether codes are producing transaction relationships.
- AI Coach does not automatically revoke or modify billing without user action.

### Phase 7 - Account join/merge flow post-MVP

Goal: handle the person who created their own account first but later needs to join a Team Leader's team or brokerage.

Jake's requirement:

- Not MVP.
- Original data/transactions stay with the agent account from their original role as Admin.

Design:

1. Let existing user request to join another organization.
2. Keep original organization and its transactions intact.
3. Add membership in the target organization if multi-membership is supported.
4. Or create a controlled transfer/invite flow with explicit data boundaries.
5. Do not silently merge data.
6. Billing updates only after owner/admin approval.

This may require a larger multi-tenant membership model if the current code assumes one user belongs to one tenant.

---

## 11. Compliance And Audit Requirements

### 11.1 Vendor sponsorship proof

Every sponsored transaction needs:

- Vendor organization.
- Vendor category.
- Individual vendor user, if selected.
- Partner code.
- Written agreement.
- Terms snapshot.
- Transaction link timestamp.
- Who attached the vendor.
- Fee split snapshot.
- Billing obligation.
- Revocation state, if later revoked.

### 11.2 No hidden steering

The product must avoid hidden commercial steering.

Rules:

- AI suggestions cannot pretend a paid vendor is recommended purely by workflow logic.
- Sponsored ads are labeled.
- Partner-code fee splits are visible to appropriate admins.
- Compliance exports explain why a vendor paid or did not pay.

### 11.3 Real-estate vendor review

Before launch, get review for:

- RESPA/settlement-service concerns.
- Referral-fee rules.
- Lender/title/vendor advertising rules.
- State-specific real-estate rules.
- Tax handling for vendor subsidies.
- Subscription terms and cancellation.
- Data privacy for cross-organization links.

This plan is not legal advice. It is a product and engineering plan that creates the audit trail legal/compliance reviewers will need.

---

## 12. What Is MVP vs Post-MVP

### 12.1 MVP or near-term

- Fix phone masking.
- Fix Company/Brokerage carry-over.
- Add account type dropdown.
- Let self-signups correct account type during onboarding.
- Keep owner/Admin protection.
- Keep invited/transaction-created roles locked.
- Add core SaaS subscription billing.
- Add entitlements.
- Add Organization -> Billing.
- Keep existing payment module separate from SaaS billing.

### 12.2 Foundation now, full build later

- Organization type.
- Vendor category.
- TC as vendor category.
- Transaction vendor links as first-class/auditable records.
- Billing per organization.
- Source anchors for partner-code future.

### 12.3 Post-MVP

- Vendor organization self-service.
- Vendor organization paid plans.
- Partner code issuance and revocation.
- Written agreement storage.
- Transaction fee split.
- Vendor budgets and limits.
- AI Coach relationship reports.
- Existing account joins another brokerage/team.
- Brokerage/Broker manual setup automation.

---

## 13. Recommended First Build Slice

The first slice should be small and revenue-aligned:

1. Fix onboarding bugs:
   - Phone mask.
   - Company/Brokerage carry-over.

2. Add account type:
   - Signup dropdown.
   - Step 2 correction.
   - Owner/Admin permission protection.

3. Add organization type foundation:
   - `organization_type`.
   - `account_type`.
   - `vendor_category` where applicable.

4. Build core SaaS billing:
   - Stripe subscription checkout.
   - Billing customer/subscription mirror.
   - Customer portal.
   - Entitlements.
   - Organization -> Billing.

5. Add upgrade prompts:
   - Staff seat limit.
   - Team features.
   - AI Coach disabled state.

Do not include in the first slice:

- Partner codes.
- Transaction fee split.
- Vendor budgets.
- AI Coach relationship intelligence.
- Account merge/join flow.

Why:

- It answers Jake's immediate signup confusion.
- It creates real subscription revenue capability.
- It protects the vendor organization future.
- It keeps Jan's solo-dev workload bounded.

---

## 14. Data Flow Examples

### 14.1 Agent self-signup

```text
User selects Agent at signup
  -> system creates solo agent workspace
  -> user permission role is Owner/Admin
  -> user account_type is Agent
  -> onboarding Step 2 shows Agent and lets them correct it
  -> billing trial starts
```

### 14.2 Mortgage vendor self-signup

```text
User selects Mortgage Vendor at signup
  -> system creates vendor organization shell
  -> user permission role is Owner/Admin
  -> user account_type is Mortgage Vendor
  -> vendor_category is mortgage
  -> vendor billing plan can be attached later
```

### 14.3 Agent uses vendor code

```text
Vendor org issues code ROCKET-SAM-20 to Sam Agent
  -> Sam accepts code
  -> Sam starts transaction
  -> Sam selects Rocket Mortgage as lender vendor
  -> system sees active code from Rocket
  -> transaction_vendor_link is created
  -> fee split snapshot is stored
  -> Rocket owes configured share
```

### 14.4 Agent has code but does not attach vendor

```text
Sam has ROCKET-SAM-20
  -> Sam starts transaction
  -> Sam does not attach Rocket Mortgage
  -> code is not eligible
  -> Rocket owes nothing
  -> Sam/owner organization covers full fee
```

### 14.5 TC starts transaction

```text
TC user from Meridian TC organization starts wizard
  -> TC selects Agent / agent organization
  -> system creates transaction with Agent as owner/primary party
  -> Meridian TC organization is attached as TC vendor
  -> any eligible TC partner code is applied
```

---

## 15. Definition Of Done

The rewritten revenue foundation is complete when:

1. New self-signups can choose an account type.
2. Self-signups can correct account type during onboarding.
3. Owner/Admin protection remains intact.
4. Invited and transaction-created users cannot self-change assigned roles.
5. Company/Brokerage carries from signup to onboarding.
6. Phone masking no longer drops digits.
7. Organizations have a type that can support vendor organizations later.
8. Vendor category can represent mortgage, title, and transaction coordination.
9. SaaS subscription billing can convert a trial to paid.
10. Subscription status drives entitlements.
11. Portal users remain non-billable.
12. Vendor organization, partner code, and transaction fee split models are documented and do not require rewriting the core tenant model later.
13. Jake can see how the partner-code monetization model will work even if it is not MVP.
14. Jan can build the first slice without needing to build the entire post-MVP vendor marketplace.

---

## 16. Source Anchors

This plan is grounded in:

- Jake's testing notes and monetization comments included in the 2026-06-05 prompt.
- Jan's responses explaining the current organization, owner/Admin, invitation, and role model.
- `requirements.txt`:
  - Payment processing.
  - Stripe payment module.
  - Advertising and monetization.
  - AI Coach paid add-on.
- `SYSTEM_DESIGN.md`:
  - Multi-tenant architecture.
  - Revenue trend analytics.
  - Advertising module for monetization.
  - AI Coach as future paid feature.
- `MILESTONE_5_2_IMPLEMENTATION_PLAN.md`:
  - Existing payment strategy.
  - Explicit exclusion of platform SaaS billing.
  - Default position of no platform fee at MVP.
- `MULTI_TENANCY_IMPLEMENTATION_PLAN.md`:
  - Staff seats.
  - Tenant plan model.
  - Open plan-tier and trial-length decisions.
- `MILESTONE_6_2_IMPLEMENTATION_PLAN.md`:
  - Advertising packages.
  - Stripe reuse.
  - Sponsored slot safety model.
- Current source foundations:
  - `velvet-elves-backend/supabase/migrations/20260512094000_tenant_plan_seats_and_grandfather.sql`
  - `velvet-elves-backend/supabase/migrations/20260512095000_seat_check_function.sql`
  - `velvet-elves-backend/supabase/migrations/20260726090000_milestone_5_2_payments.sql`
  - `velvet-elves-frontend/src/pages/organization/OrganizationPage.tsx`
  - `velvet-elves-frontend/src/pages/platform/PlatformTenantDetailPage.tsx`
  - `velvet-elves-frontend/src/pages/platform/PlatformAdvertisingPage.tsx`

---

## 17. Bottom Line

Jake's vendor-code idea makes sense and should be protected in the architecture, but it should not be crammed into MVP.

The immediate build should fix onboarding, separate account type from permission role, preserve founder/Admin safety, and add proper SaaS billing. At the same time, the foundation should recognize vendor organizations as future first-class customers. That means mortgage companies, title companies, and TC companies can later have their own users, issue their own codes, set their own budgets, attach to transactions, and pay their agreed share only when they are actually linked to a deal.

For Jan as the solo developer, the path is:

1. Fix the signup/onboarding issues that block trust.
2. Build the subscription billing foundation.
3. Add organization type and vendor category now.
4. Save partner codes, vendor-funded splits, and AI Coach relationship reporting for a deliberate post-MVP revenue milestone.

That gives Jake the monetization path he wants without forcing a risky rewrite or overloading the current MVP.
