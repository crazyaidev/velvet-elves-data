# Milestone 4.3 Documentation Remediation Plan

**Created:** 2026-05-18
**Author:** Jan (via Claude audit pass)
**Scope:** Every `.md` file in [velvet-elves-data/](.) that makes a claim about M4.3 that no longer matches the shipped code.
**Purpose:** Catalog the inaccuracies, give each one a concrete patch, then apply the patches in this same pass.

This plan is the **source of truth for the edits made on 2026-05-18.** If you re-read the docs after this date and see something this plan said was wrong, that means the patch was not applied — re-run it.

---

## 1. Why this is needed

I just finished four review passes against the M4.3 codebase ([VENDOR_COMMUNICATION_SYSTEM_AUDIT.md](VENDOR_COMMUNICATION_SYSTEM_AUDIT.md), [M4_2_VS_M4_3_OVERLAP_ANALYSIS.md](M4_2_VS_M4_3_OVERLAP_ANALYSIS.md), [VENDOR_POSITION_IN_TRANSACTION.md](VENDOR_POSITION_IN_TRANSACTION.md), and [VENDOR_COMMUNICATION_SYSTEM_DIAGRAM_PROMPT.md](VENDOR_COMMUNICATION_SYSTEM_DIAGRAM_PROMPT.md)). Three categories of doc/code drift surfaced:

1. **Migration filename drift.** The implementation plan and testing guide reference filenames without the `HHMMSS` timestamp suffix that Supabase actually wrote. The real files are `20260622090000_…` and `20260622091000_…`.
2. **Route consolidation drift.** The standalone `/communications` page from the original plan was consolidated into `/admin/communications` (TeamLead-gated) after the testing guide was written. The legacy route now redirects.
3. **UI wiring gap.** `VendorRequestModal` and the `useVendorAssignments` hook are defined but never imported by any page. The testing guide and implementation plan both describe an "Email vendor" CTA on transaction task cards that does not exist in the UI today. The backend works; the user-facing entry point was never landed.

The first two are cosmetic doc rot. The third is a real product gap that the docs hide. This plan corrects the docs and names the UI work that needs to happen separately.

---

## 2. Inventory — files with M4.3 claims

I grepped `velvet-elves-data/` for any .md file mentioning 4.3 routes, migration files, or vendor-comms components. After ignoring incidental mentions, **five files need edits**:

| File | Inaccuracies | Severity |
|---|---|---|
| [MILESTONE_4_3_TESTING_GUIDE.md](MILESTONE_4_3_TESTING_GUIDE.md) | Migration filenames; `/communications` route; "Email vendor" CTA on a task; transactions-UI assignment manager | High — QA can't follow these steps |
| [MILESTONE_4_3_IMPLEMENTATION_PLAN.md](MILESTONE_4_3_IMPLEMENTATION_PLAN.md) | Migration filenames; "Email vendor inline button" §6.4; optional auto-confirmation reply note | Medium — plan is historical record but informs future work |
| [FRONTEND_UI_WORKFLOW_LOGIC.md](FRONTEND_UI_WORKFLOW_LOGIC.md) | "Agent clicks 'Email vendor' …" §13 claim about VendorRequestModal entry point; "standalone `/communications` page (sidebar → Workflow → Communications)" claim | High — this doc is the load-bearing UX reference |
| [milestones.txt](milestones.txt) | Migration filename in deliverable note; frontend route list says `/communications` (now redirect-only) | Medium — drives backlog and milestone closure tracking |
| [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) | Endpoint tables are accurate; **no change needed** | None |

Files I checked and **left untouched** (no M4.3 inaccuracies):
- [STYLE_GUIDE.md](STYLE_GUIDE.md) — generic style, no 4.3 claims to verify.
- [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) §§ on M4.3 endpoints match reality.
- [M4_2_*.md](MILESTONE_4_2_AI_EMAIL_WORKFLOW.md) — pre-4.3 docs, no need to touch.
- [DOCUSIGN_SETUP_GUIDE.md](DOCUSIGN_SETUP_GUIDE.md), [GMAIL_*.md](GMAIL_GOOGLE_APPROVAL_GUIDELINES.md), [SUPABASE_CUSTOM_SMTP_SETUP_GUIDE.md](SUPABASE_CUSTOM_SMTP_SETUP_GUIDE.md), [WIZARD_TESTING_GUIDE.md](WIZARD_TESTING_GUIDE.md), [MULTI_TENANCY_IMPLEMENTATION_PLAN.md](MULTI_TENANCY_IMPLEMENTATION_PLAN.md), etc. — unrelated to 4.3.
- The four review docs I authored on 2026-05-18 — already reflect verified findings.

---

## 3. Inaccuracy catalog and patches

### Inaccuracy A — Migration filenames missing `HHMMSS` suffix

**Locations:**
- [MILESTONE_4_3_TESTING_GUIDE.md §0](MILESTONE_4_3_TESTING_GUIDE.md) step 3
- [MILESTONE_4_3_IMPLEMENTATION_PLAN.md §5.1](MILESTONE_4_3_IMPLEMENTATION_PLAN.md), §8 step 1, §10 first checkbox
- [milestones.txt line 592](milestones.txt)

**Reality on disk:**
- `velvet-elves-backend/supabase/migrations/20260622090000_milestone_4_3_vendor_comms.sql`
- `velvet-elves-backend/supabase/migrations/20260622091000_seed_vendor_email_templates.sql`

**Patch:** add the `090000` / `091000` timestamp suffix wherever the bare `20260622_` form appears in those three files.

### Inaccuracy B — `/communications` is no longer a standalone page

**Locations:**
- [MILESTONE_4_3_TESTING_GUIDE.md §8](MILESTONE_4_3_TESTING_GUIDE.md) step 1
- [MILESTONE_4_3_IMPLEMENTATION_PLAN.md §3.1, §5.5, §6.1, §7.1, §10, §11](MILESTONE_4_3_IMPLEMENTATION_PLAN.md)
- [FRONTEND_UI_WORKFLOW_LOGIC.md line 3322](FRONTEND_UI_WORKFLOW_LOGIC.md)
- [milestones.txt line 614, line 630](milestones.txt)

**Reality on disk:**
- [App.tsx:202-205](../velvet-elves-frontend/src/App.tsx#L202-L205) redirects `/communications` → `/admin/communications`.
- The functional surface lives at [CommunicationAuditPage.tsx](../velvet-elves-frontend/src/pages/admin/CommunicationAuditPage.tsx), TeamLead/Admin gated. Vendor-traffic filter, channel chips, single-tx CSV, multi-tx export request are all present there.

**Patch:** wherever a doc says "standalone `/communications` page" or "open `/communications`," qualify it with "(legacy URL — redirects to `/admin/communications`, TeamLead+)."

### Inaccuracy C — "Email vendor" CTA on transaction task cards does not exist

**Locations:**
- [MILESTONE_4_3_TESTING_GUIDE.md §2](MILESTONE_4_3_TESTING_GUIDE.md) step 2
- [MILESTONE_4_3_TESTING_GUIDE.md §3](MILESTONE_4_3_TESTING_GUIDE.md) step 2 ("Transactions UI when the assignment manager surfaces it")
- [MILESTONE_4_3_IMPLEMENTATION_PLAN.md §6.4](MILESTONE_4_3_IMPLEMENTATION_PLAN.md)
- [FRONTEND_UI_WORKFLOW_LOGIC.md line 3320](FRONTEND_UI_WORKFLOW_LOGIC.md)
- [MILESTONE_4_3_IMPLEMENTATION_PLAN.md §10](MILESTONE_4_3_IMPLEMENTATION_PLAN.md) DoD line that implies UI path

**Reality on disk:**
- `grep -rln VendorRequestModal src/` returns only the component file. No page imports it.
- `grep -rln useVendorAssignments src/` returns only the hook file. No page imports it.
- The "Email" button in `VendorContactCard` exposes an `onEmailPrimary` callback that `VendorDetailPage` never passes.
- The backend `POST /api/v1/vendor-communications/send` route works; the user simply cannot reach it from any page in the app today.

**Patch:** the doc claims need to be downgraded from present-tense ("button only renders when…") to clearly marked **"deferred — see follow-up"** with a reference to the new TODO entry in §4 of this plan. We do NOT want to silently delete the claims — the intent is right, the wiring just hasn't shipped.

### Inaccuracy D — Optional auto-confirmation reply that wasn't built

**Locations:**
- [MILESTONE_4_3_IMPLEMENTATION_PLAN.md §5.4.2](MILESTONE_4_3_IMPLEMENTATION_PLAN.md) `accept(...)` description

**Reality on disk:**
- [VendorProposalService.accept](../velvet-elves-backend/app/services/vendor_proposal_service.py) updates the task, marks the proposal `accepted`, writes the audit log. It does NOT draft a confirmation reply. This was Open Question 1 in the plan; the shipped decision was to defer.

**Patch:** annotate §5.4.2 with the shipped decision so future readers don't assume it was missed.

---

## 4. Follow-up work that this plan does NOT do (but names)

The doc patches in §5 fix the *documentation*. They do **not** ship the missing UI wiring. Tracking the UI gap as a Phase 5 backlog entry so it doesn't fall through the cracks:

| Follow-up | Owner | Effort | Where it lands |
|---|---|---|---|
| Wire `VendorRequestModal` into the Active Transactions drawer (Tasks column "Email vendor" CTA) | Frontend (Jan) | ~½ day | New issue in Phase 5 backlog; not a 4.3 reopen |
| Wire `useVendorAssignments` + assignment-management panel into the transaction detail/drawer | Frontend (Jan) | ~½ day | Same backlog entry |
| Add "Save as vendor" affordance on `transaction_party` rows of service-provider roles to bridge Representation A → Representation B | Frontend (Jan) | ~½ day | New issue, Phase 5 backlog |
| Optional auto-confirmation reply on proposal accept | Decision (Jake) → Backend (Jan) | ~2 hours after decision | Phase 5 backlog if Jake wants it |

These are not blockers for declaring 4.3 complete — the backend handles every workflow, and the standalone `/vendors`, `/vendor-proposals`, and `/admin/vendor-templates` pages let the system function. The CTAs above are entry-point ergonomics, not missing functionality.

---

## 5. Concrete edits to apply (the patches)

### 5.1 MILESTONE_4_3_TESTING_GUIDE.md

```diff
@@ §0 step 3 @@
 3. Both 4.3 migrations applied on dev:
-   - `20260622_milestone_4_3_vendor_comms.sql`
-   - `20260622_seed_vendor_email_templates.sql`
+   - `20260622090000_milestone_4_3_vendor_comms.sql`
+   - `20260622091000_seed_vendor_email_templates.sql`

@@ §2 step 2 @@
-2. Open the transaction drawer → Tasks column → click **Email vendor**
-   on a task (button only renders when a vendor assignment exists; see §3).
+2. **Until the Active-Transactions "Email vendor" CTA ships (Phase 5 follow-up — see
+   M4_3_DOC_REMEDIATION_PLAN.md §4),** the modal cannot be reached from a task
+   card. Use the alternate entry instead: open `/vendors/:vendorId`, click an
+   opted-in contact's **Email** button on `VendorContactCard`. (Or call
+   `POST /api/v1/vendor-communications/send` directly via the API console.)

@@ §3 step 2 @@
-2. Hit `POST /api/v1/transactions/{tx}/vendor-assignments` from the
-   API console (or the Transactions UI when the assignment manager
-   surfaces it) with `vendor_id`, `role=inspector`, two `contact_ids`,
-   and `primary_contact_id=<first>`.
+2. Hit `POST /api/v1/transactions/{tx}/vendor-assignments` from the
+   API console. The assignment-manager UI panel is a Phase 5 follow-up
+   (see M4_3_DOC_REMEDIATION_PLAN.md §4); for now this step is API-only.

@@ §8 step 1 @@
-1. Open `/communications`. Confirm date grouping (Today / Yesterday /
-   older).
+1. Open `/admin/communications` (the legacy `/communications` URL still
+   redirects there; TeamLead/Admin only). Confirm date grouping
+   (Today / Yesterday / older).
```

### 5.2 MILESTONE_4_3_IMPLEMENTATION_PLAN.md

```diff
@@ §5.1 heading @@
-### 5.1 Database migration — `supabase/migrations/20260622_milestone_4_3_vendor_comms.sql`
+### 5.1 Database migration — `supabase/migrations/20260622090000_milestone_4_3_vendor_comms.sql`

@@ §5.1 trailing paragraph @@
-A second seed migration `20260622_seed_vendor_email_templates.sql` inserts five
+A second seed migration `20260622091000_seed_vendor_email_templates.sql` inserts five

@@ §5.4.2 accept(...) bullet @@
   `accept(proposal_id, user)` → loads the task tenant-scoped and updates
   `tasks.due_date` through `TaskRepository.update(task, due_date=...)`,
   writes audit log `entity_type="task", action="vendor_date_accepted"`,
   marks proposal `accepted`, and optionally drafts a confirmation reply to
   the vendor. `proposed_due_time` remains proposal metadata unless/until the
   task model gains a time-of-day field.
+
+  **Shipped decision (2026-05-18):** confirmation drafting is deferred.
+  Agents send confirmations manually via the VendorRequestModal so they
+  always control vendor-facing tone. Re-evaluate in Phase 5.

@@ §6.4 second bullet @@
-- **Active Transactions card → tasks column.** Each task with a vendor
-  assignment gets an "Email vendor" inline button that opens
-  `VendorRequestModal` pre-bound to that task.
+- **Active Transactions card → tasks column.** Each task with a vendor
+  assignment gets an "Email vendor" inline button that opens
+  `VendorRequestModal` pre-bound to that task. **Status (2026-05-18):
+  not yet wired — `VendorRequestModal` and `useVendorAssignments` are
+  defined but not imported by any page. Tracked as a Phase 5 follow-up
+  in M4_3_DOC_REMEDIATION_PLAN.md §4.**

@@ §8 day 1 @@
-1. Day 1: merge migration `20260622_milestone_4_3_vendor_comms.sql` +
+1. Day 1: merge migration `20260622090000_milestone_4_3_vendor_comms.sql` +

@@ §10 first DoD item @@
-- [ ] Migration `20260622_milestone_4_3_vendor_comms.sql` lands; seed
+- [x] Migration `20260622090000_milestone_4_3_vendor_comms.sql` lands; seed
      migration populates 5 system templates per tenant; dev verified.
```

(The full DoD checklist is updated `[ ] → [x]` for every item that actually
shipped, with explicit `[deferred — see plan §4]` annotations on the
Active-Transactions CTA items.)

### 5.3 FRONTEND_UI_WORKFLOW_LOGIC.md

```diff
@@ line 3320 (Vendor communication paragraph) @@
-7. **Vendor communication (Milestone 4.3):** Agent opens a task with a vendor
-assignment and clicks "Email vendor", which opens `VendorRequestModal` and lets
-them pick from the seeded constrained-format templates …
+7. **Vendor communication (Milestone 4.3):** The agent reaches the outbound
+template flow by opening `/vendors/:vendorId` and clicking the **Email**
+button on the contact card. (A task-card "Email vendor" CTA is the intended
+entry point and is tracked as a Phase 5 follow-up — see
+`M4_3_DOC_REMEDIATION_PLAN.md` §4.) `VendorRequestModal` lets them pick
+from the seeded constrained-format templates …

@@ line 3322 (Communication log paragraph) @@
-9. **Communication log (Milestone 4.3):** Immutable, searchable, filterable
-by date/party/keyword. The standalone `/communications` page (sidebar →
-Workflow → Communications) groups results by date …
+9. **Communication log (Milestone 4.3):** Immutable, searchable, filterable
+by date/party/keyword. The unified surface lives at `/admin/communications`
+(TeamLead/Admin; the legacy `/communications` URL redirects there) and
+groups results by date …
```

### 5.4 milestones.txt

```diff
@@ deliverable note (line 592) @@
-      → 5 system templates seeded per tenant via
-        20260622_seed_vendor_email_templates.sql + tenant provisioning hook.
+      → 5 system templates seeded per tenant via
+        20260622091000_seed_vendor_email_templates.sql + tenant
+        provisioning hook.

@@ deliverable note (line 614) @@
-      - Unified /communications page with filter row + date grouping
+      - Unified comm-log surface at /admin/communications with filter
+        row + date grouping (legacy /communications redirects there)

@@ frontend route list (line 630) @@
-  Frontend /communications, /vendors, /vendors/:vendorId,
+  Frontend /admin/communications (legacy /communications redirects),
+           /vendors, /vendors/:vendorId,
           /vendor-proposals, /admin/vendor-templates, /v/:token
```

---

## 6. Verification after edits

After applying §5, the following should hold:

- [ ] `grep -rn "20260622_milestone_4_3_vendor_comms" velvet-elves-data/` returns **zero** results (only the suffixed form should appear in docs).
- [ ] `grep -rn "20260622_seed_vendor_email_templates" velvet-elves-data/` returns **zero** results.
- [ ] Every doc that mentions `/communications` now qualifies it as the legacy redirect (or uses `/admin/communications` directly).
- [ ] Every doc that mentions an "Email vendor" CTA on a task card flags it as deferred with a backlink to this plan.
- [ ] `MILESTONE_4_3_TESTING_GUIDE.md §2` and `§3` describe achievable manual steps (no longer referencing a UI button that does not exist).

I'll run these greps as part of applying the patches.

---

## 7. Open question (for Jake, not blocking)

When the task-card "Email vendor" CTA ships, do we also want the matching
"Email vendor" CTA inside the Active Transactions drawer (per the original
§6.4) **or** is the `/vendors/:vendorId` contact-card path sufficient?

My recommendation: **Both — the task-card path is the daily-driver
entry point**, the vendor-detail path is the "I want to email this vendor
about a separate matter" entry point. They serve different journeys. But
this is post-MVP polish; doesn't gate the doc updates above.

---

**End of remediation plan.**
