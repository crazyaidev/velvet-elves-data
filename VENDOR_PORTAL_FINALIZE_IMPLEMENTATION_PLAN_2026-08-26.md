# Vendor Portal — finalize implementation plan (2026-08-26)

**Status:** Plan only. No source was changed for this document.  
**Goal:** Close every product gap named in `VENDOR_PORTAL_LOGIC_WORKFLOW_REVIEW_2026-08-26.md` and `VENDOR_PORTAL_STANDALONE_SETTINGS_REVIEW_2026-08-26.md` so the portal is a standalone partner application (job + account), without staff chrome.  
**Constraints:** Do not restyle `VendorWorkspaceLayout`. Do not remount `AppLayout` or `/settings` for Vendor. Do not let vendors PATCH deal dates or see staff notification buckets. Keep Client Profile-only.

---

## 0 · Locked design decisions

| Decision | Choice | Why |
| --- | --- | --- |
| Settings IA | Expand **Account modal** on the vendor tree. Never mount `SettingsHubPage`. | Workspace cards are brokerage admin. |
| Account rail | Profile · Notifications · Security · Help & tour. No Sharing. | FSBO shape minus listing share-links. |
| Password | Reuse `POST /api/v1/users/password-reset/request` (same as `FsboSecurityPane`). | API already exists; do not invent in-app password PATCH. |
| Notifications | New vendor feed + prefs under `/api/v1/vendor-portal/*`. Staff `GET /notifications/pending` stays empty for Vendor. | FSBO pattern (`/dashboard/fsbo/notifications`), not staff prefs matrix. |
| Date updates | `POST /vendor-portal/files/{id}/date-update` → `VendorProposalService.propose_from_portal()`. | Plan §8.4; `inbound_log_id` is already nullable. |
| Tour | Wrap vendor routes in `TourProvider` + `<ProductTour />`. Rewrite `vendorSteps`. | Current steps target AppLayout hooks vendors never see. |
| J3 AI auto-close | Do **not** turn on. Change vendor Tasks copy to “your coordinator” until a tenant enables auto-close (staff setting). | Default is off (`VendorCommsSettings.ai_autoclose_enabled`). |
| J6 task-family column | **Out of this sprint** (follow-up). Keyword wall stays. | Residual risk, not blocking standalone. |
| Layout / visual | No redesign. Add a compact bell on the existing white rail / mobile header only. | Prior instruction: functional, not restyle. |

---

## 1 · Issue → work item map

| ID | Issue | Phase | Done when |
| --- | --- | --- | --- |
| L1 | Date update is only a note | **A** | Proposal row on Vendor Proposals; deal dates unchanged until Accept |
| L2 | Tour targets staff chrome | **B** | First-run + Help replay complete without skipped targets |
| L9 / S1 | Account is Profile-only | **B** | Rail = Profile, Notifications, Security, Help |
| S2 | No in-portal password | **B** | Security pane emails reset link |
| S3 | No `/portal/vendor/settings` | **B** | Bookmark opens Account over Files; `/settings` still bounces |
| S4 | Help Center is staff-only; tour cannot run | **B** + **G** | TourProvider on vendor tree; partner Help copy |
| L3 | `?panel=upload` / `?view=uploads` dead | **C** | Query strings open Documents tab / picker |
| L4 | Needs Attention tile vs pill disagree | **C** | Pill uses `stats.needs_attention`; list still max 4 |
| L5 | Needs Attention = overdue tasks only | **C** | Mix of overdue tasks, awaiting requests, pending close-outs; CTA deep-links the item |
| L6 | Helper cards mis-wired | **C** | Dates → file `#dates`; history → file `#activity` |
| L10 | “Velvet AI or your coordinator” oversells AI | **C** | Copy says coordinator (AI only if we later read a public flag) |
| L7 | Notes / doc requests do not ping staff | **D** | Coordinator gets an in-app `notifications` row |
| 3.2 / S5 | No vendor bell or prefs | **D** | Bell + prefs + emit on share / assign / review |
| Title coverage | verify6 was mortgage-only | **E** | Title Chrome pass documented |
| L8 / J6 | Keyword scope heuristic | **F** (optional follow-up) | Authored `vendor_scope` |
| Leftover AppLayout vendor nav | Dead `Document Requests` / `My Uploads` config | **C** (cleanup) | Config unused (vendors bounce); delete or leave — not user-facing |

---

## 2 · Phase A — Date updates are proposals (L1)

**User-visible:** Key dates still look the same. Composer gains a **required date** plus optional note. Toast: “Date sent for coordinator review.” Staff Vendor Proposals shows a **via portal** chip.

### A.1 Backend

**New method** `VendorProposalService.propose_from_portal(...)` in `app/services/vendor_proposal_service.py`.

Signature (concrete):

```
async def propose_from_portal(
    self, *, tenant_id, transaction_id, vendor_id,
    proposed_due_date: date, task_id: str | None,
    note: str | None, created_by_user_id: str,
) -> VendorProposal
```

Behavior:

- `inbound_log_id=None`, `draft_log_id=None`.
- `status="pending"` when `proposed_due_date` is set (400 if missing).
- `metadata_json = { "origin": "portal", "note": note or "", "created_by_user_id": ... }`.
- If `task_id` given: load task in tenant + same `transaction_id`; 404 if missing; set `original_due_date` from that task.
- If `task_id` omitted: best-effort match using existing `_match_task` keywords against **vendor-visible** tasks only (`is_task_visible_to_family`); unmatched still inserts with `task_id=None` (queue already supports unmatched + deal search).
- Reuse `_proposals.create(...)` (nullable inbound already).
- Audit `vendor_proposal_created` with summary containing `origin=portal`.
- **Never** call `TaskRepository.update` / never write `transactions.closing_date`.

**New endpoint** in `app/api/v1/vendor_workspace.py`:

`POST /api/v1/vendor-portal/files/{transaction_id}/date-update`  
`require_exact_roles(Vendor)` + `assert_can_act_on`.

Body (`VendorDateUpdateCreate` in `app/schemas/vendor_workspace.py`):

```
proposed_date: date          # required YYYY-MM-DD
note: str | None = None      # optional, max ~500
task_id: str | None = None   # optional; must be vendor-visible on this file
key_date_label: str | None   # optional hint ("Appraisal", "Closing") for match
```

Resolve `vendor_id` from `deal.vendor_id`. Return the proposal id + `status` + `proposed_due_date` (do not return staff-only fields).

**Staff UI chip:** `VendorProposalCard.tsx` — if `proposal.metadata_json.origin === 'portal'`, show a small “via portal” pill next to the existing status badge. Email-origin rows unchanged. `source_email` may be null; card must not crash (guard the expandable email block).

**Accept/Reject:** reuse existing `VendorProposalService.accept` / `reject`. On accept/reject, Phase D will notify the vendor; wire that in D, not here. Phase A may leave a TODO comment at those two return points.

### A.2 Frontend

`src/hooks/useVendorPortal.ts` — `usePostVendorDateUpdate(transactionId)` → POST above; invalidate `['vendor-portal']`.

`KeyDatesPanel` in `src/components/vendor-portal/VendorLoanCard.tsx`:

- Stop calling `usePostVendorNote` with `Date update: …`.
- Composer: date `<input type="date">` required; optional textarea; optional select of key-date labels (from `dates[].label`) mapped to `key_date_label`.
- Keep the existing “Submit a date update” button and panel chrome (no layout redesign).
- Success toast: “Date sent for coordinator review.”

`src/pages/vendor/VendorFileDetailPage.tsx` — if it embeds the same panel, it inherits the hook change.

### A.3 Tests

Backend (`app/tests/test_vendor_portal_api.py` + unit on service):

- Happy path: 201/200, row in `vendor_proposals` with `inbound_log_id is None`, `metadata.origin == portal`.
- Vendor cannot hit another tenant’s file (403).
- Task on another family / not visible → 404 if `task_id` forced.
- Missing date → 400.
- After submit, task `due_date` unchanged until staff accept (existing accept test still applies).

Frontend: unit test KeyDatesPanel no longer POSTs `/note` for this action (optional; API test is the gate).

`src/tests/unit/vendorProposals.test.ts` — origin chip helper if extracted.

### A.4 Acceptance

Mortgage vendor submits a date → coordinator sees it on **Intelligence → Vendor Proposals** with via-portal chip → Accept updates the task date → vendor Key dates refresh after staff accept (existing overview fetch).

---

## 3 · Phase B — Standalone Account (L2, L9, S1–S4)

**User-visible:** Chip **Account** (not Profile). Modal rail: Profile, Notifications (prefs grid; feed comes in D), Security, Help & tour. `/portal/vendor/settings` opens the modal. First-run tour spotlights real vendor nav.

Notifications **pane** in this phase can render the prefs matrix against a stub/empty feed; the bell and emit land in Phase D. If D slips, prefs GET/PUT must still persist.

### B.1 Split Client vs Vendor in AccountModal

`src/components/account/AccountModal.tsx` `railItemsForRole`:

- `Client` → `[PROFILE_ITEM]` (unchanged).
- `Vendor` → Profile, Notifications, Security, Help (`VENDOR_ITEMS`).
- `renderActive`: `notifications` → `VendorNotificationsPane` when role is Vendor (not `NotificationsSection`, not `FsboNotificationsPane`). `security` → `VendorSecurityPane` (or `FsboSecurityPane` with a `copy="vendor"` prop). `help` → `HelpSection` with vendor copy **or** `VendorHelpPane`.

Do **not** add Sharing.

### B.2 Panes (`src/components/account/sections/PortalSections.tsx`)

**VendorSecurityPane:** copy of `FsboSecurityPane`; title “Change the password you use to open your partner portal.” Same `POST /api/v1/users/password-reset/request` with `{ email: user.email }`.

**VendorNotificationsPane (prefs only in B; bind feed in D):**

- GET/PUT `/api/v1/vendor-portal/settings` (new, see D.1; ship the settings half here so the pane is not a lie).
- Matrix: email + in_app only. Categories listed in D.1.
- Reuse `NotificationPrefsMatrixGrid`.

**Help:** extend `HelpSection` with `user.role === 'Vendor'` copy (partner Files / Documents / Tasks; Help Center link). “Start tour” calls `closeModal()` then `startTour('Vendor')`. **Requires TourProvider on this tree** or `useTour()` throws.

### B.3 Tour on the vendor shell

`src/App.tsx` vendor group:

```
<RoleRoute allowedRoles={['Vendor']}>
  <AccountModalProvider>
    <TourProvider>
      <VendorWorkspaceLayout />
      <AccountModal />
      <ProductTour />
    </TourProvider>
  </AccountModalProvider>
</RoleRoute>
```

`VendorWorkspaceLayout.tsx`:

- Add `data-tour` on nav buttons: `nav-files`, `nav-documents`, `nav-tasks`.
- Add `data-tour="vendor-account"` on the user-chip button.
- After Phase D: `data-tour="vendor-bell"` on the bell.
- Copy AppLayout first-run effect (`isTourPending` / `hasSeenTour` / `persistTourState`), **including Vendor** (AppLayout currently skips only Client, but vendors never reach AppLayout).

Rewrite `vendorSteps` in `src/components/tour/tourSteps.tsx`:

| Step | Target | Copy |
| --- | --- | --- |
| files | `[data-tour="nav-files"]` | Assigned loan/title files |
| documents | `[data-tour="nav-documents"]` | Shared / your uploads / request |
| upload | `[data-tour="upload-document"]` | Put `data-tour="upload-document"` on Documents **Upload** button |
| tasks | `[data-tour="nav-tasks"]` | Mark done → coordinator review |
| account | `[data-tour="vendor-account"]` | Profile, password, alerts |
| bell | `[data-tour="vendor-bell"]` | **Gate this step** until the bell exists (Phase D). Until then omit it. |
| finale | existing `portalFinaleStep` | Keep |

Remove targets `nav-uploads`, `topbar-notifications`.

### B.4 Chip + bookmark

`UserChip`: label **Account**; `account.open('profile')`. Keep Help Center + Log out.

`src/utils/constants.ts`: `VENDOR_SETTINGS: '/portal/vendor/settings'`.

`src/App.tsx`: route `path={ROUTES.VENDOR_SETTINGS}` inside the vendor layout → `OpenAccountModalRoute` (same as `/client/settings`). `getLandingRoute(Vendor)` is already `/portal/vendor`, so the modal opens over Files.

`isAllowedForRole('Vendor')` already allows `/portal/vendor*`.

`SettingsRouter.tsx`: fix the comment — Vendor does **not** use `/settings`. Keep AppLayout bounce.

Tests: extend `src/tests/unit/FsboAccountModal.test.tsx` pattern → `VendorAccountModal.test.tsx` asserting rail labels. `returnLocation.test.ts` already expects Vendor `/settings` false; add `/portal/vendor/settings` true.

### B.5 Acceptance

Vendor opens Account → four rails. Security sends reset email (202). Help Center still opens in a new tab. Start tour highlights Files / Documents / Tasks / Account without skipped steps. `/portal/vendor/settings` opens the modal. `/settings` still redirects to `/portal/vendor` **without** staff hub.

---

## 4 · Phase C — Honest home and links (L3–L6, L10)

No new tables.

### C.1 Query strings (L3)

`VendorFilesPage`: on mount, if `panel=upload` or `view=uploads` (or `view=requests`), `<Navigate to={ROUTES.VENDOR_DOCUMENTS + search} replace />`.

`VendorPortalDocumentsPage`:

- Read `useSearchParams()`.
- `view=uploads` → tab `'uploads'`; `view=requests` or `view=awaiting` → `'awaiting'`; default unchanged.
- `panel=upload` → set tab to uploads **and** programmatically click/open the existing Upload control (`data-tour="upload-document"`). Use a `useEffect` + ref; do not restyle the picker.

Clean leftover AppLayout vendor sidebar items (`Document Requests` / `My Uploads`) **or** leave them (unreachable). Prefer delete the `case 'vendor'` nav block and `handlePrimaryCta` `upload-document` branch so they cannot rot again.

### C.2 Needs Attention (L4, L5)

`get_vendor_overview` in `app/api/v1/vendor_workspace.py`:

Build `attention` from, in order:

1. Overdue **visible** tasks (`kind=task`, `priority=high`) — existing.
2. Awaiting document requests for this vendor (`kind=document`, `priority=waiting`) — from the same `communication_logs` the Documents page already lists.
3. Pending `vendor_task_actions` (`kind=task`, `priority=due_soon`, title “Close-out in review”) so in-review work is visible on home.

`stats.needs_attention = len(attention)` (full count).  
`needs_attention = attention[:4]` (display cap).

Extend `VendorAttentionItem` with optional `href: str | None` (or derive on the client from `kind` + ids). Frontend `UrgentCard`:

- `kind=task` + overdue → `/portal/vendor/tasks` (or file detail `#task-{id}` if that hash is added).
- `kind=document` → `/portal/vendor/documents?view=awaiting`.
- pending close-out → `/portal/vendor/tasks`.
- Pill next to “Needs Attention”: **`data.stats.needs_attention`**, not `needs_attention.length`.

### C.3 Helper cards (L6)

`VendorFilesPage` HelperCard `to`:

| Card | `to` |
| --- | --- |
| Upload requested documents | `/portal/vendor/documents` (keep) |
| Keep your dates current | first file `/portal/vendor/files/{id}#dates` (fallback Files home if none) |
| Shared update history | first file `/portal/vendor/files/{id}#activity` |

`VendorLoanCard` / file detail: `id="dates"` on Key dates section, `id="activity"` on activity. On hash, expand the card if the home card starts collapsed.

### C.4 J3 copy (L10)

`VendorPortalTasksPage.tsx` (both strings ~lines 68 and 211): replace “routed to Velvet AI or your coordinator” with “routed to your coordinator, who confirms it before the task closes.”

Do not call staff `useVendorCommsSettings` from the portal.

### C.5 Tests

Overview API: mixed attention list; `stats.needs_attention >= len(needs_attention)`; cap 4.  
Frontend: helper `to` unit if extracted; Documents page tab from search params (light test).

### C.6 Acceptance

`/portal/vendor?panel=upload` lands on Documents with Upload armed. Home hero “6” and pill “6” with four cards. Helper “dates” opens Key dates. Tasks page does not mention Velvet AI.

---

## 5 · Phase D — Notifications both directions (3.2, L7, S5)

This is the load-bearing standalone piece. Pattern: FSBO bell (`app/services/fsbo_workspace.py` `list_fsbo_bell_notifications` + `notifications` table), **not** `GET /notifications/pending`.

### D.1 Prefs API (ship with B if possible)

`app/services/notification_prefs_service.py` — add vendor slice next to `FSBO_*`:

```
VENDOR_CATEGORY_KEYS = (
    "file_assignment",      # assigned / invited to a file
    "document_action",      # doc shared with you; your request shared/declined
    "task_closeout",        # close-out approved or sent back
    "task_due",             # overdue / due-today vendor-visible task (optional digest)
    "coordinator_note",     # coordinator posted on file activity (optional)
)
VENDOR_CHANNELS = ("email", "in_app")
```

`project_prefs_for_vendor` / `clip_vendor_prefs_update` — never accept `ai_email_sent`, `daily_summary`, `milestone_share_viewed`.

New endpoints on vendor-portal router (Vendor only):

| Method | Path | Role |
| --- | --- | --- |
| GET | `/api/v1/vendor-portal/settings` | Vendor |
| PUT | `/api/v1/vendor-portal/settings` | Vendor |
| GET | `/api/v1/vendor-portal/notifications` | Vendor |
| POST | `/api/v1/vendor-portal/notifications/mark-seen` | Vendor |

Settings response: `{ prefs, categories, channels, boundary_notice }` (no sharing block).

Do **not** use `/api/v1/fsbo/settings` or `/api/v1/notifications/preferences` from the vendor UI.

### D.2 In-app feed

Table: existing `notifications` (`user_id`, `tenant_id`, `kind`, `subject`, `body`, `transaction_id`, `document_id`, `read_at`).

Helper `app/services/vendor_notify.py` (new, small):

```
async def notify_vendor_user(..., user_id, kind, subject, body, transaction_id, document_id=None)
async def notify_staff_on_deal(..., transaction_id, kind, subject, body)
```

Staff recipients: transaction’s assigned TC and buyer’s agent (same people who already get deal work). Swallow errors (FSBO/client pattern). Honor `should_notify` for vendor email/in_app after prefs exist.

Feed assembler `list_vendor_bell_notifications(user, supabase)`:

- Rows where `user_id == vendor` and `kind` in vendor set.
- Synthetic optional: overdue visible tasks not yet acked (or skip synthetics in v1 and only persist rows — **prefer persist-only** so unread is honest).
- Each item: `{ id, kind, title, body, transaction_id, document_id, task_id?, href, read, created_at }`.
- `href` map:

| kind | href |
| --- | --- |
| `file_assignment` | `/portal/vendor` or `/portal/vendor/files/{tx}` |
| `document_shared` / `document_request_resolved` | `/portal/vendor/documents` |
| `task_closeout_approved` / `task_closeout_rejected` | `/portal/vendor/tasks` |
| `coordinator_note` | `/portal/vendor/files/{tx}#activity` |

Mark-seen: set `read_at` on listed ids (mirror `mark_fsbo_bell_seen`).

### D.3 Emit points (backend)

| Event | Hook | Vendor notify | Staff notify |
| --- | --- | --- | --- |
| Assigned to file | `transaction_vendor_assignments` create / invite accept | `file_assignment` | — |
| Document shared | `share_document_with_vendor` in `transaction_vendor_assignments.py` | `document_shared` | — |
| Vendor request marked shared/declined | same file when `request_id` updates | `document_request_resolved` | — |
| Close-out approved/rejected | `vendor_task_reviews.py` `approve_review` / `reject_review` | `task_closeout_*` | — |
| Date proposal accepted/rejected | `VendorProposalService.accept` / `reject` | optional `task_closeout` or `date_decision` | — |
| Vendor file note | `post_file_note` | — | `vendor_note` |
| Vendor document request | `request_document` | — | `vendor_document_request` |

Staff kinds must **not** appear in `GET /notifications/pending` task buckets. They are rows on the `notifications` table the staff topbar already knows how to show **if** `kind` is one the staff panel lists. Check `NotificationsPanel` / `computeUnreadNotificationCount`. If staff bell ignores unknown kinds, either:

- map staff ping to a kind the panel already displays (e.g. communications), **or**
- add `vendor_note` / `vendor_document_request` to the staff panel filter.

**Do not** widen `get_pending_notifications` for Vendor.

Email: if `should_notify(..., channel="email")`, send via existing `platform_mailer` (short “You have an update in Velvet Elves” + deep link). If mailer plumbing is heavy, **v1 in-app only** with prefs stored; email in a fast follow. Call this out in QA: prefs save even if email is queued later.

### D.4 Frontend bell

`src/utils/vendorBell.ts` — clone `fsboBell.ts` kinds/filters/empty copy (“When the team shares a document or sends back a task, it shows up here.”).

`useVendorBellNotifications` / `useMarkVendorBellSeen` in `useVendorPortal.ts` or `useNotifications.ts`.

`VendorWorkspaceLayout`:

- Desktop: bell button above the user chip (or in the chip row) with unread badge. `data-tour="vendor-bell"`.
- Mobile header: same control.
- Panel: reuse `FsboNotificationsFeed` patterns (tabs all/unread) in a vendor-named component. Opening an item navigates `href` and mark-seen.
- Do **not** mount `NotificationsPanel` (staff/FSBO/attorney switchboard).

Account → Notifications pane: prefs matrix from D.1. Do not embed the full feed twice; prefs only in the modal, feed in the bell.

### D.5 Tests

- Prefs PUT clips staff keys.
- Non-vendor 403 on vendor-portal settings/notifications.
- Share-document creates a notification for the assignment’s portal user.
- Approve/reject close-out creates vendor notification.
- Note + document request create staff notification for the TC.
- `GET /notifications/pending` as Vendor still empty buckets.
- Frontend: vendor bell unread helper unit tests (like `fsboBell.test.ts`). `useUnreadNotificationCount` must not use staff pending for Vendor.

### D.6 Acceptance

Coordinator shares a doc → vendor bell + (if enabled) email. Vendor marks task done → staff approve → vendor sees “approved” in the bell without polling. Vendor posts a note → coordinator sees an in-app item. Account Notifications saves email/in-app toggles.

---

## 6 · Phase E — Title + regression Chrome QA

Do not call the portal final on mortgage-only verify6.

**Harness:** `velvet-elves-data/vendor_portal_qa/` (existing). Duplicate Tessa script for a **title** assignment user (or seed one). Same headless Chrome, 1280×720.

**Scripts to cover:**

1. Title family: Title Files label, title tasks/docs/contacts, no mortgage-only tiles leaking, no seller if still hidden.
2. Mortgage regression (Tessa): upload bound to file, mark done / undo, Account rails, tour, date-update → staff queue (if staging has a coordinator login in the same run, or API assert).
3. Multi-file vendor if available: Needs Attention cap, helper `#dates` uses a real file id.
4. Sent-back: staff reject close-out → vendor Tasks shows reason + bell.
5. `/portal/vendor?panel=upload`, `/portal/vendor/settings`, `/settings` bounce.
6. Empty state: vendor with zero files (if fixture exists).

Write results to a new `VENDOR_PORTAL_CHROME_QA_<date>.md`. Fix blockers before calling E done.

---

## 7 · Phase F — Optional follow-up (L8 / J6)

**Not in the finalize sprint.** When scheduled:

- Add `tasks.metadata_json.vendor_scope` (`mortgage` \| `title` \| `shared` \| `internal`) or a real column.
- Admin mapping UI on Task Templates (plan Phase 5).
- `is_task_visible_to_family` checks authored scope first, keywords as fallback.
- Migration backfill from current keyword function so behavior does not flip overnight.

---

## 8 · Phase G — Partner Help Center article (S4 content)

Independent of code deploy order; can ship after B.

Add article slug `vendor-partner-portal` in help-center seed SQL (`supabase/migrations/*help_center*`): Files / Documents / Tasks, mark done, request a document, date proposals, Account password and alerts. Audience = Vendor, not “Vendor Directory” for agents.

`HelpSection` vendor copy: “Partner-portal articles open in a new tab.” Link can stay `HELP_CENTER_URL` until the article is live; in-modal tour still works.

Do not rewrite staff vendor-communication articles.

---

## 9 · Suggested build order and commits

```
A  date-update proposal          backend + KeyDatesPanel + via-portal chip
B  Account rail + tour + bookmark  can start in parallel with A after schemas frozen
C  home honesty + query params + J3 copy
D  notify helper + emit hooks + bell + prefs (prefs endpoint may land in B)
E  Chrome title + regression
G  help article (anytime after B copy exists)
F  J6 later
```

**Do not** start D UI until D.1 kinds are named (href map). **Do not** add the tour bell step until the bell is in the layout.

Suggested commit subjects (user commits; agent does not):

1. `feat(vendor): submit date updates as Vendor Proposals`
2. `feat(vendor): Account rail with security, help, and a real tour`
3. `fix(vendor): honor upload deep links and Needs Attention counts`
4. `feat(vendor): partner bell, prefs, and coordinator pings`
5. `docs(vendor): title Chrome QA and partner Help article`

---

## 10 · Files to touch (checklist)

### Backend

- `app/services/vendor_proposal_service.py` — `propose_from_portal`
- `app/api/v1/vendor_workspace.py` — date-update, overview attention, settings + notifications routes
- `app/schemas/vendor_workspace.py` — `VendorDateUpdateCreate`, attention `href`, settings/bell schemas
- `app/services/notification_prefs_service.py` — `VENDOR_*` slice
- `app/services/vendor_notify.py` — **new**
- `app/api/v1/transaction_vendor_assignments.py` — notify on share / assign
- `app/api/v1/vendor_task_reviews.py` — notify on approve/reject
- `app/tests/test_vendor_portal_api.py`, `test_vendor_workspace.py`, new notify tests
- Help SQL migration (Phase G)

### Frontend

- `src/components/vendor-portal/VendorLoanCard.tsx` — date composer; `#dates`
- `src/pages/vendor/VendorFilesPage.tsx` — redirect query, helpers, pill, UrgentCard href
- `src/pages/vendor/VendorPortalDocumentsPage.tsx` — search params, `data-tour="upload-document"`
- `src/pages/vendor/VendorPortalTasksPage.tsx` — J3 copy
- `src/hooks/useVendorPortal.ts` — date-update, settings, bell
- `src/components/account/AccountModal.tsx` + `PortalSections.tsx`
- `src/layouts/VendorWorkspaceLayout.tsx` — Account label, data-tour, bell, first-run tour
- `src/App.tsx` — TourProvider + ProductTour + settings route
- `src/components/tour/tourSteps.tsx`
- `src/components/vendors/VendorProposalCard.tsx` — via portal
- `src/utils/constants.ts`, `src/utils/vendorBell.ts` (**new**)
- `src/layouts/AppLayout.tsx` — delete dead vendor nav/CTA (optional)
- Tests: `VendorAccountModal.test.tsx`, `vendorBell.test.ts`, `returnLocation.test.ts`

### Explicitly do not touch

- `settingsCards.ts` / `SettingsHubPage.tsx` (no vendor cards)
- Staff `/notifications` page allow-list (keep Vendor out)
- Client `railItemsForRole`
- Visual tokens of the white vendor rail beyond a bell control

---

## 11 · Definition of done

A tester (mouse, no staff login as the vendor) can:

1. Log in as mortgage **and** title; each sees only their family.
2. Submit a date; it appears on staff Vendor Proposals with **via portal**; Accept changes the task date; the vendor never wrote the deal row.
3. Mark done → In review → Undo; staff reject → Sent back + bell.
4. Receive a bell item when a document is shared or a file is assigned; prefs disable email without hiding the rail.
5. Complete the tour with no missing-target skip.
6. Email a password reset from Account → Security.
7. Open `/portal/vendor?panel=upload` and `/portal/vendor/settings`; `/settings` bounces to the portal.
8. Home Needs Attention count matches the pill; helper dates land on Key dates.

Until 2–6 are true, the portal remains a scoped workspace, not a finished standalone partner app.

---

## 12 · Related documents

- `VENDOR_PORTAL_LOGIC_WORKFLOW_REVIEW_2026-08-26.md` — L1–L10  
- `VENDOR_PORTAL_STANDALONE_SETTINGS_REVIEW_2026-08-26.md` — Account vs Settings hub  
- `VENDOR_WORKSPACE_SUPERIOR_PLAN.md` §6.2, §8.3–§8.4, Phase 7  
- `VENDOR_PORTAL_CHROME_QA_2026-08-26.md` — mortgage verify6 baseline  
