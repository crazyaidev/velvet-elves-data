# Attorney Workspace — specialized-scope fix plan

**Date:** 2026-08-15  
**Depends on:** `ATTORNEY_WORKSPACE_SCOPE_FINDINGS.md`  
**Goal:** Counsel cannot reach default-workspace pages (All Documents, Contacts, Calendar, AI Suggestions, Analytics, AI email outbox, Task Queue, Email & E-signature, My Playbook) from Search, Notifications, settings, typed URLs, or post-login return. Notifications on the desk are legal-queue alerts only.

Do not add “new matter.” Do not restore Agent chrome on the counsel desk.

---

## 1. Search

### Frontend — `SearchPalette.tsx`

- Hide `go-documents` when `isAttorney` (same pattern as Task Queue / Create transaction).
- Request `types=transaction,document` for Attorney.
- Relabel the transaction section **Matters** for Attorney.
- Drop task/contact hits client-side as a safety net.
- Navigate via `counselSearchHref` → `/transactions/{id}?section=review&tab=needs-call`. Hits without a matter id are omitted.

### Backend — `app/api/v1/search.py`

- If `current_user.role == Attorney`: discard `task` and `contact` from `requested`.
- Matter hits: `href = /transactions/{id}?section=review&tab=needs-call`.
- Document hits: same matter href when `transaction_id` is set; skip unattached docs.
- Agent hrefs unchanged.

### Tests

- Vitest: Attorney quick-action ids exclude `go-documents` / `go-task-queue` / `new-transaction`.
- Vitest: `counselSearchHref` maps transaction + document hits onto the matter workspace.
- Pytest: Attorney search returns matter hrefs and no `/documents` or `/contacts` or task types.

---

## 2. Notifications

### Backend — `GET /api/v1/notifications/pending`

- Attorney short-circuit: empty task lists, `ai_drafts_pending=0`, `external_communications_today=0`. Do not call `list_pending_ai_drafts`.

### Frontend

- Bell and `/notifications`: when role is Attorney, render a **counsel feed** from `useAttorneyDashboard().matter_cards` (Need review / Ready to release). Rows open `counselMatterHref`. No AI Drafts banner, no outbound-email banner, no Overdue/Today/Tomorrow task tabs.
- Unread badge for Attorney = count of need-review + ready matters (work waiting), not AI drafts.
- Hide Morning Digest on Settings → Notifications for Attorney.

### Tests

- Pytest: Attorney pending payload has zero drafts and empty task buckets even if drafts exist in the tenant.
- Vitest: `computeUnreadNotificationCount` still counts drafts for Agent; counsel attention count ignores drafts.

---

## 3. URL isolation

Move these routes from `INTERNAL_AND_ATTORNEY` to `INTERNAL_ROLES` in `App.tsx`:

- `/documents`, `/documents/all`
- `/calendar`
- `/contacts`
- `/ai-suggestions`
- `/analytics`, `/reports`
- `/settings/connections`, `/settings/my-playbook`

Keep on `INTERNAL_AND_ATTORNEY` (or Attorney-only):

- Transaction list + `/transactions/:id`
- Settings account / notifications / help
- `/attorney/releases`, `/attorney/state-rules`, `/attorney/recording-calendar`

Also:

- `DocumentsPage` inner allow-list → `INTERNAL_OPS_ROLES` (belt and suspenders). Do **not** change `DocumentsModal` (in-matter docs stay).
- `/profile` redirect: Attorney → `/settings/account`; others keep reports.
- `RoleRoute` fallback remains `/dashboard` (DashboardRouter sends Attorney to `/dashboard/attorney`).

### Return URLs — `returnLocation.ts`

Attorney allow-list:

- `/dashboard/attorney`
- `/transactions` and `/transactions/*`
- `/attorney/*`
- Universal: settings, notifications, terms, privacy

Remove documents, contacts, calendar, analytics, AI suggestions.

---

## 4. Settings

- `settingsCards.ts`: `connections.visible` excludes Attorney.
- My Playbook / Email Templates already hidden — keep.
- Settings hub may still open for Attorney (Profile, Notifications, Help & Tour only).

---

## 5. Copy / comments that caused the drift

- `roles.ts`: `INTERNAL_PLUS_ATTORNEY` is transaction list + matter detail only.
- `App.tsx` comments on Documents / Calendar / Contacts / Intelligence.
- Product docs after implementation (see §7).

---

## 6. Chrome retest

Rebuild frontend `dist`, keep preview on `:5173`. Re-run `attorney_scope_chrome_qa.mjs` with wait-for-auth on each `goto` so a denied route is scored as desk vs Agent page, not as `/login`.

Must pass:

1. Search has no **Open All Documents**.
2. Search hit click stays on `/transactions/{uuid}`.
3. Bell has no **AI draft** / outbound-email copy.
4. Typed `/documents`, `/calendar`, `/contacts`, `/ai-suggestions`, `/reports`, `/ai-emails`, `/settings/connections` land on the Attorney desk (or Attorney settings), never the Agent page, never login.
5. Counsel URLs (`/dashboard/attorney`, `/attorney/releases`, `/attorney/recording-calendar`, `/settings/account`) still work.
6. Upload documents, Ask AI, sign-off chrome still present.

Fix any remaining failures before updating product docs.

---

## 7. Documentation updates (after code + Chrome pass)

- `ATTORNEY_WORKSPACE_PLAN.md` — add a “Specialized scope / isolation” section.
- `FRONTEND_UI_WORKFLOW_LOGIC.md` §5.4 — drop Attorney from All Documents allowed roles; add §7.5 Search, notifications, URL isolation.
- `SYSTEM_DESIGN.md` §3.3 — AI Suggestions for Attorney = Ask AI on assigned matters, not `/ai-suggestions`. Analytics remains No. Note that All Documents is Agent-only.
- This plan’s checkbox status in a short “Completed” note at the bottom after retest.

---

## Completed (2026-08-15)

All items above were implemented and retested.

- Frontend: search palette, counsel notifications, route gates, settings cards, return-URL allow-list, DocumentsPage inner gate, `/profile` redirect.
- Backend: Attorney search hrefs + omitted task/contact types; pending notifications short-circuit (no AI drafts, no task queue).
- Chrome: `attorney_scope_chrome_qa.mjs` → **44 pass / 0 leak / 0 fail**.
- Docs: `ATTORNEY_WORKSPACE_PLAN.md` §1.5, `FRONTEND_UI_WORKFLOW_LOGIC.md` §5.3/§5.4/§5.5/§6.1/§7.5, `SYSTEM_DESIGN.md` §3.3 and §4.3.1e isolation note.

