# Attorney Workspace — specialized-scope findings

**Date:** 2026-08-15  
**Portal:** Attorney Workspace (`/dashboard/attorney` → matter at `/transactions/:id`)  
**QA user:** `adams.jefferson@minafter.com`  
**Harness:** `attorney_portal_qa/attorney_scope_chrome_qa.mjs`  
**Artifacts:** `attorney_portal_qa/artifacts_scope_2026-08-15/`  
**Sources:** `SYSTEM_DESIGN.md` §3.3 / §4.3.1e, `FRONTEND_UI_WORKFLOW_LOGIC.md` §7, `ATTORNEY_WORKSPACE_PLAN.md` §1.1–1.4, frontend `App.tsx` / `AttorneyLayout.tsx` / `SearchPalette.tsx` / `NotificationsPanel.tsx`, backend `app/api/v1/search.py` / `notifications.py`

This document defines what belongs in the Attorney Workspace, then records every leak found in a real Chrome session and in source.

---

## 1. Specialized scope (source of truth)

The Attorney deliverable is **assigned matters** (`role_in_transaction = 'attorney'`). AI prepares the file. A human attorney signs off, holds, or releases. The desk is **not** the Agent Transaction OS.

### 1.1 In scope (counsel)

| Surface | Route / entry | Why it belongs |
|---|---|---|
| Caseload + matter workspace | `/dashboard/attorney`, `/transactions/active`, `/transactions/:id` | The desk. Sidebar is the matter list; canvas is the open file. |
| Legal packet upload | Top-bar **Upload documents** modal | Counsel intake on an existing matter. Attorney cannot create transactions. |
| Search (matters / people-on-file / docs-on-file) | ⌘K / Search | Jump **into an assigned matter**, never into Agent list pages. |
| Today's AI Briefing | Top-bar chip (and ⌘K quick action) | Opens Ask AI on the legal queue. Not the Agent Critical / Needs Attention bar. |
| Ask AI | Shared FAB, caseload- or matter-scoped | Legal queue briefing and file questions. |
| Notifications | Bell | Alerts about **assigned legal work** (need review, ready to release, holds, recording/deadlines). |
| Releases queue | `/attorney/releases` | Human-initiated packet release. |
| Recording calendar | `/attorney/recording-calendar` | Counsel recording dates — not the Agent closing calendar. |
| State rules | `/attorney/state-rules` | Closing-mode / recording / disbursement reference. |
| Personal settings | `/settings`, `/settings/account`, `/settings/notifications`, `/settings/help` | Profile, personal alert prefs, Help & Tour. |
| Account menu | Settings, Help Center, Log Out | Identity only. |
| Full notifications page | `/notifications` | Same counsel feed as the bell, not the Agent task inbox. |

### 1.2 Out of scope (default / Agent workspace)

Direct URL access is **not** permitted. Role gates must bounce counsel to `/dashboard` → Attorney landing. Typed URLs, search hits, notifications, settings cards, and post-login return URLs must not reopen these surfaces.

| Surface | Typical route | Why it is out |
|---|---|---|
| All Documents | `/documents`, `/documents/all` | Agent AI document queue. Counsel reviews docs **on the matter**. |
| Closing calendar | `/calendar` | Agent pipeline calendar. Counsel calendar is `/attorney/recording-calendar`. |
| Contacts directory | `/contacts` | Tenant Rolodex. Counsel people live on the matter People panel. |
| AI Suggestions | `/ai-suggestions` | Agent intelligence page. Counsel tool is Ask AI. |
| Analytics / reports | `/reports`, `/analytics`, `/profile` → reports | Permission matrix: Attorney has **No** analytics. |
| AI email outbox | `/ai-emails` | Agent draft-approval queue. |
| Task Queue / Needs You | `/tasks/queue`, `/needs-you` | Team task engine. |
| Payments, vendors, clients hub, sharing | `/payments`, `/vendors`, `/clients`, `/sharing` | Agent operations. |
| Email & E-signature | `/settings/connections` | Gmail / Outlook / DocuSign for Agent outbound mail. |
| My Playbook / Email Templates | `/settings/my-playbook`, `/email-templates` | Agent closing checklists and mail merge. |
| Other role dashboards | `/dashboard/agent`, `/dashboard/admin`, `/dashboard/team` | Identity dashboards. |

### 1.3 Hard rules

1. **No create-transaction** from counsel chrome or search.
2. **No AI auto-release.**
3. Search hits for matters, documents, or people must open `/transactions/{id}?section=review&tab=…`, never `/documents`, `/contacts`, or `/transactions?status=&expand=`.
4. Notifications must not mention AI drafts, outbound Agent mail, or the task-queue Overdue / Today / Tomorrow model.
5. `INTERNAL_PLUS_ATTORNEY` is **only** for transaction list + matter detail. It is not a license to share Agent workflow pages.

---

## 2. Chrome probe (pre-fix)

Login succeeded and landed on a matter:

`/transactions/4585ea3b-43d1-420e-b5d9-8193afdd3d1f?section=review&tab=needs-call`

Screenshots: `01_search_empty.png`, `02_search_hits.png`, `03_all_documents_page.png`, `04_notifications.png`.

### 2.1 Search — confirmed leak

| Check | Result | Evidence |
|---|---|---|
| Quick action **Open All Documents** | **LEAK** | Present in the empty palette. |
| Click **Open All Documents** | **LEAK** | Navigated to `http://127.0.0.1:5173/documents`. Screenshot `03_all_documents_page.png`. |
| Create new transaction | PASS | Hidden. |
| Open My Task Queue | PASS | Hidden. |
| Today's AI Briefing | PASS | Counsel-scoped chip present. |

Code match: `SearchPalette.tsx` hides Task Queue and Create transaction when `isAttorney`, but `go-documents` has **no** `visible: !isAttorney`. Backend `search.py` still emits Agent hrefs (`/documents?focus=`, `/contacts?focus=`, `/transactions?status=&expand=`).

### 2.2 Notifications — code leak; tenant-dependent in Chrome

The probe body did not contain the string "AI draft" for this user at this moment (likely `ai_drafts_pending === 0`). That is **not** a pass.

| Check | Result | Evidence |
|---|---|---|
| AI Drafts banner | **LEAK (code)** | `NotificationsPanel.tsx` renders `{n} AI drafts awaiting review` whenever `data.ai_drafts_pending > 0` and navigates to `/ai-emails?view=outbox`. Backend `GET /notifications/pending` always loads tenant-wide `list_pending_ai_drafts` with **no Attorney branch**. Unread badge includes drafts (`computeUnreadNotificationCount`). |
| Outbound emails today | **LEAK (code)** | Same pending payload + banner. |
| Overdue / Today / Tomorrow tabs | **NOTE / leak of shape** | Bell uses the Agent task-queue chrome. Clicks go to `/transactions/active?highlight=&task=` (ignored by the counsel desk) or `/tasks/queue`. |
| `/notifications` page | **LEAK (code)** | Ungated route; same Agent feed. |

This matches the reported defect: when any AI draft exists in the tenant, counsel sees an Agent outbox alert.

### 2.3 Direct URLs

| Path | Chrome result | Code truth |
|---|---|---|
| `/documents` | **LEAK** — stayed on All Documents | `RoleRoute allowedRoles={INTERNAL_AND_ATTORNEY}`. `DocumentsPage` treats Attorney as internal (`INTERNAL_PLUS_ATTORNEY`). |
| `/documents/all`, `/calendar`, `/contacts`, `/ai-suggestions`, `/reports` | Probe then bounced to `/login` | Still on `INTERNAL_AND_ATTORNEY`. After `/documents` loaded, subsequent full navigations lost the session (Agent page APIs 401 → `handleAuthFailure` logout). **Visiting All Documents as counsel can kill the session.** |
| `/tasks/queue`, `/needs-you`, `/payments`, `/vendors`, `/clients`, `/ai-emails`, other dashboards | Already `INTERNAL_ROLES` (or Attorney-only dashboards). After session death the probe recorded `/login` rather than a clean bounce to the desk. | Gates exist; they must send counsel to the Attorney landing, not login. |
| `/settings/connections`, `/settings/my-playbook` | Hub hides Playbook card; Connections card is `visible: () => true`. Routes still `INTERNAL_AND_ATTORNEY`. | Typed URL opens Email & E-signature. |
| `/profile` | Not hit in Chrome | Hard `Navigate` to `/reports?scope=me` (analytics). |

### 2.4 Settings hub

Attorney `shellVariant` is `internal`, so Settings is the **internal card grid**, not the portal Account modal. Visible personal cards today: Profile, Notifications, **Email & E-signature**, Help & Tour. Email & E-signature is Agent Gmail/DocuSign.

Morning Digest on `/settings/notifications` is the Agent task digest.

---

## 3. Additional source leaks (not all visible in one Chrome pass)

1. **Search hrefs** (`app/api/v1/search.py`): transaction → `/transactions?status=<bucket>&expand=<id>` (AttorneyWorkspacePage ignores `expand` and `pickLandingMatter`s). Document → `/documents?focus=`. Contact → `/contacts?focus=`. Task hits are still searched for Attorney.
2. **Return-URL allow-list** (`returnLocation.ts` `isAllowedForRole('Attorney')`) still allows `/documents`, `/contacts`, `/calendar`, `/analytics`, `/ai-suggestions`. After logout from All Documents, re-login can restore that Agent URL.
3. **`roles.ts` comment** claims documents, calendar, and contacts are shared with Attorney. That comment is how the drift recurred.
4. **Unread badge** counts tenant AI drafts for every role.
5. **Analytics** is Yes for Agent and **No** for Attorney in `SYSTEM_DESIGN.md` §3.3, yet `/reports` is on `INTERNAL_AND_ATTORNEY`.
6. **AI Suggestions** is listed as “Attorney-relevant” in the 2026 matrix; the shipped desk uses Ask AI. The standalone page is Agent chrome.

---

## 4. Integrity verdict

The Attorney Workspace chrome (navy caseload, matter canvas, Upload documents, Ask AI) is specialized. **Search, notifications, route gates, settings cards, and post-login return URLs still share Agent workspace surfaces.** The two reported defects are real, and they are instances of one rule: counsel must not reach the default workspace by click, search, notification, or typed URL.

The remediation plan is `ATTORNEY_WORKSPACE_SCOPE_FIX_PLAN.md`.

---

## 5. Post-fix Chrome retest (2026-08-15)

Harness: `attorney_portal_qa/attorney_scope_chrome_qa.mjs` after implementing the plan.

**Result: 44 pass / 0 leak / 0 fail / 46 checks.**

Confirmed:

- Search has no **Open All Documents**. Query `oak` opens `/transactions/{id}?section=review&tab=needs-call` under a **Matters** heading.
- Bell shows Need review / Ready (legal queue). No AI Drafts, no outbound email, no Overdue tab.
- Typed `/documents`, `/calendar`, `/contacts`, `/ai-suggestions`, `/reports` (via `/analytics`), `/ai-emails`, `/settings/connections`, `/settings/my-playbook` bounce to `/dashboard/attorney` with Attorney Workspace chrome. Session stays logged in.
- Counsel URLs (`/attorney/releases`, recording calendar, settings, notifications) still work.
- Settings hub shows Profile, not Email & E-signature / My Playbook.
- Account menu remains Settings / Help Center / Log Out.

