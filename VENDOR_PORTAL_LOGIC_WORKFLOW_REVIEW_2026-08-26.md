# Vendor Portal — logic, workflow, and finalize review (2026-08-26)

**Status:** Analysis only. No source was changed for this document.  
**Audience:** Product / QA deciding what to finish before calling the Vendor Portal done.  
**Sources:** Live frontend (`VendorWorkspaceLayout`, `/portal/vendor*`), live backend (`/api/v1/vendor-portal/*`), `VENDOR_WORKSPACE_SUPERIOR_PLAN.md`, `FRONTEND_UI_WORKFLOW_LOGIC.md` §9.5, `VELVET_ELVES_CURRENT_FEATURE_LIST_2026-08-25.md` §16, Chrome QA `VENDOR_PORTAL_CHROME_QA_2026-08-26.md`, and the Client / FSBO / staff shells for comparison.

**Tester context:** Mortgage vendor `tessa.grant@minafter.com` on 4567 Meadowridge Avenue. Chrome verify6 was **42/42** on the happy path after the 26 Aug scope/upload/bounce fixes. That pass proves the core loop works; it does **not** prove the portal is complete or that every Jake/plan surface is honest.

---

## 0 · Verdict in one page

| Question | Answer |
| --- | --- |
| 1. Logic / workflow errors? | **Yes.** Several are real product mismatches, not just polish. The portal is usable, but a few paths do not do what their labels (or the plan) claim. |
| 2. All necessary functions? | **The daily job is there** (see files, tasks, documents, close-out, note, request, upload). **Notifications are a genuine gap.** Date updates, onboarding tour, and account settings are incomplete vs Jake’s spec and vs FSBO. |
| 3. Do existing functions help, and operate perfectly? | **They help** a mortgage officer who already knows to open Files / Documents / Tasks. **They do not operate perfectly:** some CTAs are mis-wired, Needs Attention is incomplete, close-out waits on staff (by design until J3), and there is no “something happened while you were away” surface. |

**Recommendation for finalize:** treat this as a **workflow-complete v1** only after the P0 items in §6. Do not add staff chrome (Task Queue, AI Emails, `/notifications` as built for agents). Add a **vendor-scoped** bell and email prefs instead.

---

## 1 · How the portal actually works today

A Vendor never uses `AppLayout`. Login lands on `/portal/vendor` inside `VendorWorkspaceLayout`.

```
Login (Vendor)
  → Files home  (greeting + stats + Needs Attention + assigned loan/title cards)
      → expand card / Open file  → tasks, key dates, contacts, documents, activity
  → Documents   (shared / uploads / requests, Upload, Request a document)
  → Tasks       (grouped by file, Mark done → pending review, Undo)
  → Account     (Profile only: name, email, photo)
```

**Nav:** `{Loan|Title|Your} Files · Documents · Tasks` (parametric by `scope_family`). Mobile: Files / Docs / Tasks / More.

**API wall:** `/api/v1/vendor-portal/*` is `require_exact_roles(Vendor)` plus assignment scope. Mortgage vendors see buyer-side contacts and mortgage-family tasks; coordinator checklist items (HOA, thank-yous, gifts) are hidden after the 26 Aug scope wall.

**What a successful day looks like for Tessa**

1. See Meadowridge on Files, badge **Appraisal Ordered**.
2. Open Needs Attention or Tasks, expand **Appraisal Completed**.
3. Mark done with a note (“Appraisal received”) → status **In review** until a coordinator approves on **Intelligence → Vendor Proposals** (`VendorTaskReviewQueue`).
4. Upload or request a document on Documents; it is bound to the assigned file.
5. Send a file note to the coordinator from the expanded card.

Chrome QA confirmed that loop for one mortgage deal. Title vendors, multi-file vendors, and “sent back” close-outs were not exercised in that pass.

---

## 2 · Question 1 — Logic and workflow errors

These are mismatches between what the UI promises and what the system does, or between two surfaces on the same page.

### L1 · “Submit a date update” is only a note

**Where:** Expanded file card → Key dates → “Submit a date update”.

**Plan (`VENDOR_WORKSPACE_SUPERIOR_PLAN` §8.4):** create a `vendor_proposals` row via `propose_from_portal()`, origin `portal`, so it appears on **Vendor Proposals** with Accept / Reject. Dates must never write straight to the deal.

**As built:** the button posts `POST /vendor-portal/files/{id}/note` with body `Date update: …`. There is **no** `/date-update` endpoint. Nothing lands in the proposals queue. The coordinator may never see it unless they read that deal’s communication log.

**Impact:** High. The label says “update”; the system files a sticky note. Staff who watch Vendor Proposals will think no date work arrived.

### L2 · Guided tour still describes the old thin portal

**Where:** `tourSteps.tsx` `vendorSteps`.

Tour targets `[data-tour="nav-documents"]`, `nav-uploads`, `upload-document`, and `topbar-notifications`. Those attributes live on **staff `AppLayout`**, which vendors no longer see (RoleRoute + bounce to `/portal/vendor`). Copy still says “Document Requests”, “My Uploads”, and a bell with a red dot.

**Impact:** High for first-run. A new vendor’s tour points at missing chrome and teaches the wrong nav.

### L3 · Deep links `?panel=upload` and `?view=uploads` are dead

**Where:** Documented in `FRONTEND_UI_WORKFLOW_LOGIC.md` §9.5 and still used in leftover `AppLayout` vendor nav config.

**As built:** `VendorFilesPage` / `VendorPortalDocumentsPage` do not read those query params. `/portal/vendor?panel=upload` is just Files home.

**Impact:** Medium. Emails or old bookmarks that used the query string fail silently.

### L4 · Needs Attention count disagrees with the tiles

Overview API returns `stats.needs_attention =` full overdue-task count, but `needs_attention` is **sliced to 4**. Files home:

- Hero tile uses `stats.needs_attention` (e.g. 6).
- Section pill uses `needs_attention.length` (max **4**).

**Impact:** Medium. The page argues with itself when there are more than four overdue items.

### L5 · Needs Attention is only overdue tasks

**Plan §5.1:** up to four cards covering overdue task, requested document, date confirmation, and an open request. Each primary button should deep-link to **that** task or document.

**As built:** cards are built only from overdue scoped tasks. CTA is always **Open file** (file detail), not `/portal/vendor/tasks` or a task hash. Awaiting document requests never appear here.

**Impact:** Medium. The “five-second” strip cannot represent document or date work.

### L6 · Helper cards go to the wrong places

| Card | Promise | Actual `to` |
| --- | --- | --- |
| Upload requested documents | Documents | Documents — correct |
| Keep your dates current | Confirm appraisal / financing / closing dates | Files **home**, not the Key dates panel |
| Shared update history | Requests sent and received on the file | **Tasks** page, not file activity |

**Impact:** Low–medium. Users who trust the cards miss the composer they were sent for.

### L7 · Notes and document requests do not notify the coordinator in-app

`POST .../note` and `POST .../documents/request` write `communication_logs` only. They do not create a row in the staff notification bell or a Vendor Proposals item. Coordinators who live in Active Transactions / Task Queue can miss them.

**Impact:** Medium. Vendor effort can disappear into the log.

### L8 · Keyword scope is still a heuristic

Mortgage/title visibility is derived from task **name + milestone** keywords (`appraisal`, `loan`, `title`, …) plus a short shared set (clear-to-close, rate lock). There is still no `vendor_scope` column on tasks.

**Impact:** Residual. A oddly named mortgage task can stay hidden; a badly named TC task could still leak. Safer than the old “GENERIC = show everyone” rule, not equivalent to an authored map (plan J6 / Phase 5 admin mapping).

### L9 · Account modal vs staff Settings

Vendors used to leak into staff `/settings`. That is **fixed** (bounce + Profile-only Account modal). Remaining inconsistency: FSBO Account has Notifications, Sharing, Security (password); Vendor Account is **Profile only**. Password change and notification prefs have no vendor UI.

### L10 · Close-out vs Jake’s “AI then closes it”

Jake: vendor comment or upload → **AI determines completion and closes the task**.  
As built: action is **pending**; AI auto-close is **off by default** (tenant policy, pending J3). Staff approve on Vendor Proposals. Honest, but the vendor copy (“routed to Velvet AI or your coordinator”) oversells AI if the tenant never enabled it.

---

## 3 · Question 2 — Necessary functions, and what is missing

### 3.1 What v1 already covers (keep)

These match Jake’s mortgage/title intent and feature list §16:

| Function | Status |
| --- | --- |
| Scoped file list (loan vs title labeling) | Shipped |
| Expandable file: milestone strip, next step, tasks, dates (read), contacts, docs, activity | Shipped |
| Mortgage hides seller; add contact only in own section | Shipped |
| Documents: shared / uploads / awaiting, upload bound to assigned file, request a document | Shipped |
| Tasks: mark done (note or upload), Undo while pending, sent-back reason | Shipped |
| Boundary copy (“you only see requests addressed to you”) | Shipped |
| Staff bounce (`/dashboard`, `/settings`, `/ai-emails`, …) | Shipped (26 Aug) |
| Internal review of close-outs (`VendorTaskReviewQueue` on Vendor Proposals) | Shipped |

This is enough for a vendor who is **already in the app** and looking at a live file.

### 3.2 Should Notifications be in the Vendor Portal?

**Yes — a vendor-scoped notification surface, not the staff bell.**

Evidence:

1. **Jake / plan.** Phase 7: “notifications both directions.” Tour copy already promises pings when a new request arrives or a date proposal needs confirmation. File detail exists so “notifications can link straight to a task or document” (`VENDOR_WORKSPACE_SUPERIOR_PLAN` §4.2).
2. **Peer portals.** FSBO Account includes a Notifications pane (email/in-app prefs). Represented Client is Profile-only **by choice** (staff-oriented categories do not apply). Vendor is closer to FSBO: they are an outside worker who is not in the app all day.
3. **Current API.** `GET /api/v1/notifications/pending` **returns empty buckets for Vendor** on purpose (portal roles must not see tenant AI drafts or staff task buckets). `/notifications` is `RoleRoute` internal + attorney. So today a vendor has **no bell, no feed, and no prefs**.
4. **How they actually learn work exists.** Invite email (portal account). Optional “email a vendor” task mail (constrained templates). Nothing in-app when a coordinator shares a document, rejects a close-out, or assigns a new file.

**What not to ship:** the staff Notifications page (overdue/today/upcoming **internal** tasks, AI draft counts, “mail sent on your behalf”). That would leak the pipeline Jake forbade.

**What to ship (proposed):**

| Event | In-app (bell on vendor shell) | Email (opt-in) |
| --- | --- | --- |
| You were assigned / invited to a file | Deep link Files | Yes |
| A document was shared with you | Deep link Documents | Yes |
| A document request you made was shared or declined | Documents → Awaiting | Yes |
| Close-out approved or sent back | Tasks, that row | Yes |
| New overdue / due-today **vendor-visible** task | Tasks | Digest optional |
| Coordinator posted on the file activity | File detail | Optional |

Account rail: **Profile · Notifications · Security (password) · Help** — same shape as FSBO, without Sharing (vendors do not own public milestone links).

Until that exists, email from “Email a vendor” remains the only reliable ping, and it is **staff-initiated**, not a portal inbox.

### 3.3 Other essential gaps (not chrome)

| Gap | Why it is essential | vs nice-to-have |
| --- | --- | --- |
| Date **proposal** (L1) | Jake: vendors propose dates; they do not type into the deal. Notes are not reviewable. | Essential |
| Notification bell + prefs (3.2) | Outside partners will not poll Files daily. | Essential for “finalize” |
| Tour rewritten to Files / Documents / Tasks | First session currently lies. | Essential |
| Password / security in Account | FSBO has it; vendors currently cannot change password in-portal. | Essential |
| Needs Attention includes docs + requests; deep-link the item | Home is the five-second surface. | High |
| `?panel=upload` → Documents with picker open | Documented; used in leftover links. | Medium |
| Title-vendor Chrome pass | Mirror of mortgage; untested in verify6. | High before calling “done” |
| Authored task↔family map | Keyword wall will keep surprising edge cases. | Medium (J6) |
| AI auto-close decision (J3) | Copy already mentions Velvet AI. | Product call, not a bug |
| Vendor **messages** thread (like Client Messages) | File notes + email already exist. A third inbox can confuse. | Defer unless Jake wants a chat |
| Payments, calendar, Ask Aime | Out of Jake’s mortgage/title scope. | Do not add |

---

## 4 · Question 3 — Do existing functions help, and operate perfectly?

### 4.1 They do help (keep the shape)

For a loan officer the three-nav shell is easier than staff VE. Scoped tasks, no seller, upload-to-file, request-a-doc, and mark-done-with-note match how that job actually works. Chrome QA showed:

- Greeting, Meadowridge, boundary notice, mortgage family.
- Contacts with email/phone, one Tessa row, no seller.
- Upload attached to the deal; file under Your uploads.
- Mark done → pending → Undo.
- Staff URLs bounce.

Internal close-out review on Vendor Proposals is the right staff counterpart (human gate while AI auto-close is off).

### 4.2 They are not perfect

| Function | Helps? | Operates perfectly? |
| --- | --- | --- |
| Files home | Yes — one screen for “what’s mine” | Count mismatch (L4); Needs Attention too narrow (L5); helper cards (L6) |
| File detail | Yes — one card for the deal | Date CTA dishonest (L1); urgent CTA is “Open file” not the task |
| Documents | Yes — share / upload / request | Query-string upload deep link dead (L3); request may not ping staff (L7) |
| Tasks | Yes — close-out without staff login | AI wording vs pending; sent-back depends on staff using the queue |
| Notes | Yes — low-friction ping | No staff notification (L7); date notes mixed with chatter |
| Add contact | Yes — own section only | Untested in Chrome; depends on `can_add_contact_group` |
| Profile | Minimal identity | No password, no notification prefs, no Help in the rail |
| Tour | Intended to help | Points at missing staff chrome (L2) |

“Operate perfectly” also fails **coverage**: one mortgage user, one file. Title, generic vendor, zero-file empty state, reject/sent-back, and two assigned deals were not Chrome-proven.

### 4.3 What already “works well enough” for a freeze

If finalize means “mortgage v1, known gaps listed”:

- Scope wall, staff bounce, upload-must-have-file, Undo, documents tabs, mark done.
- Do **not** freeze date updates, tour, or notifications as done.

---

## 5 · Workflow map (intended vs as-built)

```
Vendor                     Coordinator (staff)
──────                     ───────────────────
See assigned file     ←──  Invite to portal + assignment
Mark done (note/doc)  ──→  Vendor Proposals close-out queue  → Approve/Reject
Upload document       ──→  Deal documents (review in staff docs)
Request a document    ──→  communication_log only (easy to miss)
Date update (UI)      ──→  communication_log note  ✗ not Vendor Proposals
File note             ──→  communication_log
                   ✗  ←──  No in-app ping when staff shares a doc or rejects
                   ✗  ←──  Optional: staff "Email a vendor" (outside portal)
```

The **broken arrows** are the finalize list.

---

## 6 · Proposed modifications (priority)

No implementation in this pass. Suggested order for a finalize sprint.

### P0 — Must fix before calling the portal final

1. **Date updates as proposals.** Implement `POST /vendor-portal/files/{id}/date-update` → `propose_from_portal()`. Keep the existing Key dates UI; change only the submit path and staff origin chip (“via portal”). Do not let vendors PATCH deal dates.
2. **Vendor notifications (in-app + email prefs).** Bell on `VendorWorkspaceLayout` (not AppLayout). Events in §3.2 only. Empty `notifications/pending` for Vendor stays empty for **staff** buckets; add a vendor-specific feed. Account: Notifications pane (FSBO-like matrix, vendor categories). Deep links to Files / Documents / Tasks / file detail.
3. **Rewrite the vendor tour** onto real targets: Loan Files, Documents (Upload + Your uploads), Tasks (Mark done), Account. Remove `topbar-notifications` until the bell exists; then point at it.
4. **Title-vendor browser pass** (same script as Tessa, title assignment). Mortgage-only green is not finalize.

### P1 — Honest home and links

5. Needs Attention: include awaiting requests and pending close-outs; cap display at 4 but show `stats.needs_attention` on the pill; CTA to the task/document, not only the file.
6. Honor `?panel=upload` / `?view=uploads` by routing to Documents and opening the right tab/picker.
7. Point helper cards at Documents, file Key dates (or file detail `#dates`), and file activity.
8. When a vendor posts a note or document request, create a **staff** in-app item the coordinator already understands (or a row on Vendor Proposals / a deal activity badge)—not only `communication_logs`.

### P2 — Account and operations

9. Vendor Account rail: Profile, Notifications, Security (password), Help. Keep Sharing off.
10. Decide J3 (AI auto-close). If off, change Tasks copy from “Velvet AI or your coordinator” to “your coordinator”.
11. Optional: authored task-family map (J6) so keywords are a fallback, not the wall.

### P3 — Explicitly out of finalize

- Staff `/notifications`, Task Queue, AI Emails, Analytics.
- Client-style Messages tab (unless Jake asks).
- Payments, calendar, Ask Aime on the vendor shell.
- Visual redesign (layout already matches the live VE system).

---

## 7 · Suggested acceptance for “final”

A tester (mouse-first) can:

1. Log in as mortgage and as title; each sees only their family of tasks/docs/contacts.
2. Submit a **date** and see it on staff **Vendor Proposals** (not only a note).
3. Mark a task done, see In review, Undo; staff reject → vendor sees Sent back without refreshing blindly.
4. Get a **bell + email** when a document is shared or a new file is assigned.
5. Complete the tour without a missing-target skip.
6. Change password from Account.
7. Open `/portal/vendor?panel=upload` and land on the upload control.

Until 2–5 are true, the portal is a **solid scoped workspace**, not a finished partner product.

---

## 8 · Related documents

- `VENDOR_WORKSPACE_SUPERIOR_PLAN.md` — Jake rules, phases, date-proposal and notification intent  
- `VENDOR_WORKSPACE_TESTING_GUIDE.md` — mouse scripts; Phases 0–6 claimed implemented; AI auto-close off  
- `VENDOR_PORTAL_CHROME_QA_2026-08-26.md` — 26 Aug Chrome findings and the scope/upload/bounce fixes  
- `FRONTEND_UI_WORKFLOW_LOGIC.md` §9.5 — route map (partially stale on `?panel=upload`)  
- `VELVET_ELVES_CURRENT_FEATURE_LIST_2026-08-25.md` §16 — shipped capability list (does not mention a vendor bell)
