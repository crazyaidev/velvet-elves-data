# Is Vendors › Directory still needed, now that Deals › Contacts exists?

**Written:** 2026-08-13  
**Question:** After reviewing Vendors › Directory, it is unclear whether that page is still useful, or whether its content now belongs on the newly built Deals › Contacts page.  
**Mode:** Research only. No application source code was changed. This file is the answer.  
**Codebases reviewed:** `velvet-elves-frontend/`, `velvet-elves-backend/`  
**Governing docs:** `requirements.txt`, `SYSTEM_DESIGN.md`, `milestones.txt`, `FRONTEND_UI_WORKFLOW_LOGIC.md`, `STYLE_GUIDE.md`  
**Companion analyses (older; some claims are now outdated — see §8):** `VENDOR_POSITION_IN_TRANSACTION.md` (2026-05-18), `VENDOR_PROPOSALS_NAV_PLACEMENT_ANALYSIS.md` (2026-06-24)  
**Live check:** platform admin `shyna.elene@minafter.com` against the local API (`http://localhost:8000`), tenant `526cf077-59da-496a-aa38-8f8d761c29da`. Production `api.prod.velvetelves.com` rejected this account (401); counts below are from the local tenant this credential actually authenticates.

---

## TL;DR

| Question | Answer |
|---|---|
| Is Vendors › Directory still needed? | **Yes.** It is the company roster, not a second people list. |
| Does its content belong on Deals › Contacts? | **No.** Contacts is the person rolodex. Directory is the company record that other vendor features hang off. |
| Why do they feel like duplicates? | They **look** alike (same collection-table chrome), and the silent vendor auto-bridge **copies service-provider people onto both**. On this tenant, 28 of 33 contacts are vendor-linked. |
| Should we delete `/vendors` or fold it into `/contacts`? | **Do not.** That would orphan preferred-vendor lists, deal assignments, colleague invites, template email, and wizard company matching. |
| What *should* change later (not in this pass)? | Clarify the person-vs-company story in the UI, and stop Contacts’ “Vendor contact” checkbox from creating an orphan person with no company row. |

**One-line recommendation:** keep both pages. Treat **Contacts** as “who to call” and **Vendor Directory** as “which firm we reuse across deals.” The confusion is information architecture, not wasted functionality.

---

## 1. Why this question is reasonable

Three things make Directory look redundant:

1. **The two pages were built to look the same.** `ContactsPage.tsx` is explicitly “matching Vendor Directory”: breadcrumb, serif title, count pill, one-line toolbar, dense table, row click → read-only modal, kebab for edit / preferred / delete (`STYLE_GUIDE.md` §15.4).
2. **Contacts already has a “Vendors” filter.** The segmented control is `All | Preferred | Vendors | Incomplete`. Filtering to Vendors shows people with `is_vendor === true` — which, after auto-bridge, is most of the directory.
3. **Deals already has two other “people” items.** Sidebar Deals is now Active / Drafts / Closed / All / **Clients** / **Contacts**. Vendors then sits as its own group with a single child, “Vendor Directory.” A thin group plus a lookalike page reads as unfinished.

The product tour already has to explain the split (`tourSteps.tsx`):

- Contacts: “Search every person… Vendor companies themselves live one group down in Vendor Directory.”
- Vendor Directory: “Lenders, title companies, inspectors, and more in one directory. Assign a vendor to a deal and request the documents or dates you need.”

That explanation exists because the overlap is real. It does not mean the company page is unused.

---

## 2. What each page actually is

These are **different entities**, not two views of one table.

### 2.1 Deals › Contacts — `/contacts`

**Page:** `velvet-elves-frontend/src/pages/ContactsPage.tsx`  
**API:** `GET/POST/PATCH/DELETE /api/v1/contacts/`  
**Row type:** a **person** (`contacts` table).

| | |
|---|---|
| Identity | `full_name` (required) |
| Classification | `contact_type` (buyer, seller, co-agent, loan officer, title rep, attorney, inspector, appraiser, home warranty, other) |
| Reach | email, phone, `mailto:` / `tel:` on the row |
| Company | free-text `company` string — **not** a foreign key |
| Flags | `is_preferred`, `is_vendor` |
| Optional link | `vendor_id` (set by auto-bridge / colleague invite; **not** set by the Contacts create form) |
| Actions | New contact, edit, mark preferred, delete (Agent / Team Lead / Admin), Export CSV, deep-link `?focus=` |
| Detail modal | Phone sheet: type, company, email, phone, state, notes. No deal list. No template email. |
| Access | Internal ops **and Attorney** (`INTERNAL_PLUS_ATTORNEY`) |
| Nav | Deals group, next to Clients |

Copy on the page: *“Everyone you work with — call, email, or update without opening a deal.”*

### 2.2 Vendors › Directory — `/vendors`

**Page:** `velvet-elves-frontend/src/pages/vendors/VendorListPage.tsx`  
**API:** `/api/v1/vendors/` plus `/contacts`, `/transactions`, `/colleague-invites`  
**Row type:** a **company** (`vendors` table).

| | |
|---|---|
| Identity | `company_name` (required) |
| Classification | `category` slug (inspector, appraiser, title_company, lender, closing_attorney, …) |
| Reach | company email, phone, **website**, address, state |
| Flags | `is_preferred`, `is_active` |
| Actions | New vendor, edit, mark preferred, **Add colleague** (public `/v/:token` invite), delete (Team Lead / Admin only) |
| Detail modal | Company card + **people on file** + **deals this firm is assigned to** + template **Email** flow (`VendorContactEmailFlow` → `VendorRequestModal`) |
| Access | Internal ops only (`Agent`, `TransactionCoordinator`, `TeamLead`, `Admin`). **Attorney has no Vendor Directory nav or route.** |
| Nav | Own **Vendors** group; sole item |

Empty-state copy: *“Add the inspectors, appraisers, title companies, and other service providers you work with so they’re reusable across every transaction.”*

There is **no** `/vendors/:id` page anymore. Detail is a modal (replacing the older detail route described in May 2026 docs).

### 2.3 Not the same as Clients, either

Deals › Clients (`ClientsHubPage.tsx`) is a third surface: **represented portal users** (questions to answer, uploads to review). It is not a rolodex and not a vendor book.

```
Clients     = people with portal access on your deals
Contacts    = every saved person (buyers, sellers, co-agents, vendor people)
Directory   = every saved vendor company (the firm, reused across deals)
```

---

## 3. What the project documents require

The spec never described a single combined “people + companies” page. It described **both**.

### 3.1 Contact directory (people)

`requirements.txt` §1.3:

> Centralized contact directory linked to transactions **and vendors**. Store details for co-agents, loan officers, title reps, attorneys, buyers, sellers. Functions to update names, emails, phone numbers. … Once connected, contacts persist for future transactions.

`SYSTEM_DESIGN.md` §2.2.4 (`contacts` table): “Requirement 1.3 — centralized contact directory linked to transactions and vendors. Contacts persist across transactions.”

Milestone 1.3: contact CRUD **and** vendor contact-card API (additional contacts, opt-in).

That is Deals › Contacts: a tenant-wide person file, including vendor *people*.

### 3.2 Vendor companies (firms)

`requirements.txt` §1.5 Agent/Team Profiles: **“Preferred vendors list.”**  
Milestone 4.3 (complete): vendor company model, `transaction_vendor_assignments`, colleague invites, background refresh, constrained-format vendor email, vendor proposals. Routes called out:

> Frontend `/vendors`, `/vendors/:vendorId`, `/vendor-proposals`, …

`FRONTEND_UI_WORKFLOW_LOGIC.md` Shared Shell: **Vendors — Vendor Directory** as its own nav group. Internal product tour includes a Vendor Directory step.

Milestone 5.3 preferred vendors (`user_preferred_vendors`, team `team_preferred_vendor_ids`) store **vendor UUIDs**, not contact IDs. The picker searches `/api/v1/vendors`.

Client decision recorded in `vendor_autobridge.py` (2026-07-13):

> “We should have a MASTER Vendor Directory in the background of every vendor ever input in every single transaction ever created.” Saving a vendor must never be an extra step.

So Directory is not a leftover list page. It is the **master company file** the wizard, parties, and preferred-vendor playbook are supposed to fill and reuse.

### 3.3 Conceptual position of a vendor

`VENDOR_POSITION_IN_TRANSACTION.md` still has the right mental model even though some wiring notes are stale:

A vendor is **not a contract party**. Buyer / seller / agents sign. A vendor is a **third-party service provider** that (1) does not sign the contract, (2) gates a deadline (inspection, appraisal, title, closing), and (3) **persists across deals**. That third property is why a company table exists. Parties are one-shot rows on one file; vendors are durable firms.

Contacts can store the *person at the firm*. They cannot be the firm.

---

## 4. Data model: how the two tables relate

```
vendors                          contacts
────────                         ────────
id                               id
company_name                     full_name
category                         contact_type
website                          company          ← plain text, not FK
email / phone                    email / phone
address / state                  state
is_preferred (company)           is_preferred (person)
is_active                        is_vendor        ← boolean, independent of a row in vendors
                                 vendor_id        ← FK to vendors (ON DELETE SET NULL)

transaction_vendor_assignments
  transaction_id + vendor_id + role

transaction_vendor_assignment_contacts
  assignment_id + contact_id (opt-in person on that deal)
```

Schema: `202603110000_new_vendors_and_ad_hooks.sql` created `vendors` and added `contacts.vendor_id`. Milestone 4.3 added assignments, colleague tokens, background refresh. Milestone 5.3 added `user_preferred_vendors`.

**Bridge that now exists** (`app/services/vendor_autobridge.py`): when a service-provider party is saved on a deal (wizard or People tab) — inspector, appraiser, title, attorney, home warranty, loan officer — the backend silently:

1. matches or creates a **vendor company** (email → phone → normalized company name),
2. matches or creates a **contact person** with `is_vendor=true` and `vendor_id` set,
3. creates a **transaction_vendor_assignment** linking that firm to the deal.

The wizard also loads both lists: `/api/v1/contacts/?page_size=200` and `/api/v1/vendors/?is_active=true&page_size=200`, and `findVendorForParty()` fills empty party fields from the **company** directory.

So the same title company can appear as:

- a **Vendor Directory** row (the firm, category `title_company`, portfolio of deals),
- one or more **Contacts** rows (the people, or sometimes the company name reused as `full_name`),
- a **party** on each deal,
- a **preferred vendor** chip in My Playbook / team settings.

Contacts is downstream of Directory for vendor firms. It is not a substitute for it.

---

## 5. Capability comparison

What you can do on each page (as built today):

| Capability | Deals › Contacts | Vendors › Directory |
|---|---|---|
| Store a **person** (buyer, seller, co-agent) | Yes — this is the home | No |
| Store a **company** (title co., lender, inspection firm) | Only as a text `company` field on a person | Yes — this is the home |
| Category (Inspector / Title Company / Lender / …) | Person **type** (different enum) | Company **category** |
| Website, address | No website; state only | Website, address, state |
| One-click call / email (`tel:` / `mailto:`) | Yes | Company email/phone on the card; people get copy + **template Email** |
| Constrained vendor request email (deal + task + template) | No | Yes, from the detail modal (`VendorContactEmailFlow`) |
| Colleague invite (`/v/:token`) | No | Yes, row kebab “Add colleague” |
| Cross-deal portfolio (“on these deals”) | No | Yes |
| Preferred flag | Person-level | Company-level (this is what Playbook uses) |
| Export CSV | Yes | No |
| Mobile compact list | Yes | Desktop table only |
| Deep-link highlight (`?focus=`) | Yes | No |
| Create form sets the other entity | “Vendor contact” checkbox sets `is_vendor` **only** — does **not** create a `vendors` row or set `vendor_id` | New vendor does **not** create a contact; people appear via auto-bridge, assignment, or colleague invite |
| `useCreateVendorContact` (add a person onto a company from Directory) | — | Hook exists; **not used by any page** |
| Background refresh UI | — | API exists; **not on the current modal** (was on the old `/vendors/:id` page) |
| Delete permission | Agent, Team Lead, Admin | Team Lead, Admin only |
| Attorney can open the page | Yes | No |
| Used by wizard autocomplete / fill | Person match | Company match (`findVendorForParty`) |
| Used by preferred-vendors picker | No | Yes (`/api/v1/vendors`) |
| Used by vendor assignments / proposals / task “vendor carts” | Indirectly (person email) | Directly (`vendor_id`) |

The overlap is **search + preferred + similar table chrome**. The Directory-only jobs are **company identity, reuse across deals, and the vendor-communications stack.**

---

## 6. Live tenant snapshot (this credential, local API)

Pulled 2026-08-13 after login as `shyna.elene@minafter.com` (role Admin).

| Metric | Count |
|---|---|
| Vendor companies (`/vendors/?is_active=true`) | **23** |
| Contacts (`/contacts/?page_size=200`) | **33** |
| Contacts with `is_vendor=true` **and** `vendor_id` set | **28** (85% of the people file) |
| Contacts with email equal to a vendor company email | **23** |
| Contacts whose `company` string equals a vendor `company_name` | **26** |
| Contacts whose `full_name` equals their `company` (firm stored as if it were a person) | **11** |
| Preferred vendors / preferred contacts | **0 / 0** |
| Vendor categories | lender 9, attorney 7, title_company 7 |
| Vendors with a website | **0** (22 of 23 have a phone) |

**Non-vendor contacts (the 5 rows Contacts uniquely owns):**

- Jordan Ellis — buyer  
- Maya Ellis — buyer  
- Inbound Test Contact — buyer  
- QA Hale 380589 — loan officer at “QA National Bank” (created from the Contacts page QA on 2026-08-13)  
- QA Hale 126638 — same pattern  

Those two QA loan officers are the smoking gun for the merge question: they were added on **Deals › Contacts** as type Loan Officer, and they **do not** appear as companies in Vendor Directory (`is_vendor` is false, no `vendor_id`). Checking “Vendor contact” on the Contacts form would still not create a firm. Only the auto-bridge (or New vendor on Directory) writes a `vendors` row.

**Per-company people and deals (Directory’s unique value):**

Examples from the same pull:

- Reliable Title Agency, Inc. — 4 people, 3 deals  
- Reliable Title & Escrow, Inc. — 2 people, 2 deals  
- Capital City Title North — 2 people, 1 deal  
- Most other firms — 1 person; several have **0 deals** (company exists in the master list even when not currently assigned)

Contacts cannot show “this title company is on three files” or “invite a colleague at this firm.” Directory can.

That is why 85% overlap in *names* does not make Directory disposable. Auto-bridge is doing what the client asked: every vendor typed on a deal lands in the master company file **and** as a person. Contacts is showing the people half of that write.

---

## 7. Does Contacts already cover Directory’s job?

### 7.1 What Contacts *does* cover

- Calling or emailing a named person without opening a deal.
- Buyers, sellers, and co-agents (Directory will never hold these).
- Filtering “incomplete” people (missing email or phone).
- CSV export of the rolodex.
- Attorney access to people.

If the only goal were “find a phone number,” Contacts would be enough for many days.

### 7.2 What Contacts cannot cover without becoming a second vendor product

1. **One firm, many people.** Directory is 1 company → N contacts. Contacts is 1 person → optional `vendor_id`. There is no company hub on `/contacts`: no website, no category filter, no “people at this firm,” no colleague link.
2. **Reuse across deals.** Assignments, wizard fill, and preferred-vendor playbooks key off `vendors.id`. Contacts IDs are not those keys.
3. **Outbound vendor workflow.** Template send requires `vendorId` + transaction + task (`VendorContactEmailFlow.tsx`). Contacts’ Email button is `mailto:` only.
4. **Opt-in / colleague card.** Milestone 4.3 contact-card feature lives on the vendor company (`POST /vendors/{id}/colleague-invites`).
5. **Vendor carts / proposals.** Task queue vendor carts and vendor-proposal matching are company-scoped.
6. **Different delete and role rules.** Folding companies into Contacts would either let Agents delete firms (today they cannot) or hide company actions from Attorney (who can see Contacts).

### 7.3 The checkbox trap

`DirectoryContactModal` offers “Vendor contact (inspector, title, lender, etc.).” That writes `is_vendor: true` and **does not** send `vendor_id` or call `POST /vendors/`. Those people then appear under Contacts → Vendors, and **never** in Vendor Directory. That is the opposite of a merge: it creates a third, unlinked definition of “vendor.”

`useCreateVendorContact` in `useVendors.ts` was written to attach a person to a company; nothing in the UI calls it.

---

## 8. What older docs got wrong (so this file supersedes them on wiring)

| Older claim | Status on 2026-08-13 |
|---|---|
| Auto-bridge from parties → `vendors` does not exist (`VENDOR_POSITION_IN_TRANSACTION.md` §2.3) | **Exists.** `vendor_autobridge.bridge_party_to_vendor` runs on service-provider party save. Client decision 2026-07-13. |
| `VendorRequestModal` is never imported | **Wired** from Directory via `VendorContactEmailFlow` on `VendorDetailModal`. Still not the primary “Email vendor” CTA on the Active Transactions task card (that follow-up remains). |
| `/vendors/:vendorId` is the detail page | **Replaced** by `VendorDetailModal` on the list. `App.tsx` has no detail route. |
| `FRONTEND_UI_WORKFLOW_LOGIC.md` Deals nav is Active / Pending / Closed / All / Clients | **Contacts was added later** (`AppLayout.tsx` comment: the page existed at `/contacts` but was missing from the sidebar). Spec nav list is behind the build. |
| Email vendor by opening `/vendors/:vendorId` | Path is now: Directory → row → modal → Email on a person. |

The older conclusion that Directory is “mostly disconnected from the deal flow” is **half true**: inbound auto-bridge and Directory email are connected; the deal-page “Email vendor” / assignment panel is still the weaker entry. That is an entry-point gap, not a reason to delete the company page.

---

## 9. Conclusions

1. **Vendor Directory is needed.** It is the master **company** file required by §1.5 preferred vendors, Milestone 4.3 vendor communications, Milestone 5.3 playbooks, and the 2026-07-13 “master directory in the background of every vendor ever input” decision.

2. **Deals › Contacts is also needed, and is not a replacement.** It is the master **person** file required by §1.3. Its job includes buyers and sellers, whom Directory must not absorb.

3. **The content does not “belong” on Contacts.** The same *names* appear on both because auto-bridge writes both tables. The *records* are different. Moving company CRUD onto Contacts would either flatten firms into people (losing 1-to-N, website, category, assignments) or hide a second schema behind a filter chip — which is how the current “Vendors” scope already confuses the page.

4. **The user’s uncertainty is a UX bug, not a scope bug.** Lookalike tables + a Contacts filter literally named “Vendors” + a thin Vendors sidebar group + auto-bridged rows that often use the company name as `full_name` (11 of 33 contacts here) make Directory feel like a duplicate. The tour text is compensating for that.

5. **Do not remove `/vendors` in a cleanup pass.** Downstream FKs: `transaction_vendor_assignments.vendor_id`, `user_preferred_vendors.vendor_id`, colleague tokens, background refresh, vendor task actions, wizard `findVendorForParty`.

---

## 10. Recommended product direction (no code in this pass)

**Keep both pages.** Optional later work, in order of leverage:

1. **Rename, don’t merge.** Contacts filter “Vendors” → “Vendor people” (or “Service providers”). Directory title stays “Vendor directory” / companies. Tour copy already says this; the filter label fights it.

2. **Stop the orphan checkbox.** Contacts “Vendor contact” should either (a) require picking/creating a company, or (b) be removed in favor of “New vendor” on Directory. Today it produces people that look like vendors and are invisible to company workflows.

3. **Link through.** On a Contacts row with `vendor_id`, show the company name as a control that opens Directory (or the vendor modal) instead of a dead string. On Directory, “Contacts” is already a list of people; those names could deep-link to `/contacts?focus=`.

4. **Do not fold Directory into Contacts as a tab unless the tab is companies.** A future “Directory” hub with **People | Companies** would reduce the thin Vendors group without collapsing the data model. That is an IA change, not a deletion.

5. **Leave Vendor Proposals in Intelligence.** That grouping question is separate (`VENDOR_PROPOSALS_NAV_PLACEMENT_ANALYSIS.md`). Directory is an address book; Proposals is an AI approval queue.

**Not recommended:** deleting Vendor Directory; treating Contacts as the system of record for firms; hiding Directory because 85% of contact rows happen to be vendor-linked on this tenant.

---

## 11. Bottom line

Vendors › Directory is still a real product surface. Deals › Contacts did not replace it. Contacts answered “I need a rolodex of people next to Clients.” Directory remains “the firm we keep, assign, email with a template, and prefer across files.”

They share chrome and, after auto-bridge, they share many names. They do not share a schema, a permission model, or a workflow. The page should stay. The labeling should get clearer when someone next touches this IA.

---

**End of analysis.**
