# Vendor Portal — standalone operation vs default-workspace Settings (2026-08-26)

**Status:** Analysis only. No source was changed for this document.  
**Question:** Can the Vendor Portal run as a standalone application using the built-in Account / Settings modal? Should we add features by copying the default workspace Settings page?  
**Sources (code first):** `AccountModal.tsx`, `VendorWorkspaceLayout.tsx`, `App.tsx`, `AppLayout.tsx`, `settingsCards.ts` / `SettingsHubPage.tsx`, `SettingsRouter.tsx`, `OpenAccountModalRoute.tsx`, `PortalSections.tsx` (FSBO Security / Notifications), `PersonalSections.tsx` (staff Notifications + Help), `ProfileSection.tsx`, `dashboardShellConfig.ts`, `returnLocation.ts`, `tourSteps.tsx`, backend `app/api/v1/users.py`, `notifications.py`, `client_fsbo_settings.py`, `notification_prefs_service.py`. Data-folder plans were used only as secondary context.

---

## 0 · Direct answers

| Question | Answer |
| --- | --- |
| Does the portal have all functions needed to be a **standalone app**? | **For the daily job, almost.** Files / Documents / Tasks, login, logout, and profile edits work without ever entering the staff workspace. **For a self-contained product** (account, password, help, “something happened while you were away”), **no.** |
| Can it operate independently **with the current Settings / Account modal**? | **Only as a thin identity overlay.** The modal is mounted on the vendor shell, but for `role === 'Vendor'` the rail is **Profile only**. That is not a Settings page. |
| Should we add features by copying the **default workspace Settings hub** (`/settings`)? | **Use it as a checklist of *kinds* of personal settings — do not mount or clone the hub.** Most cards are tenant/workspace admin. The right peer is the **FSBO Account modal**, not the Agent Settings grid, and not the represented-Client Profile-only rail the code currently copies. |

**Verdict:** The portal is already a **standalone shell**. It is not yet a **standalone account**. Finalize by expanding the existing Account modal (Profile · Notifications · Security · Help), not by giving vendors `/settings`.

---

## 1 · What “standalone” means here

Two different things get mixed:

1. **Shell independence** — a Vendor never needs `AppLayout`, Task Queue, AI Emails, or the Settings hub to do assigned work.
2. **Account independence** — a Vendor can manage identity, password, help, and alerts without leaving `/portal/vendor` or hunting public auth pages.

(1) is largely true today. (2) is not.

A third-party loan officer / title rep is closer to an **FSBO seller** (outside worker, not in VE all day) than to a **represented Client** (staff handles the file). The current Account rail treats Vendor **the same as Client**. That is the design mismatch.

---

## 2 · What is actually built (source, not docs)

### 2.1 Dedicated shell — yes

`App.tsx` mounts `/portal/vendor*` under `RoleRoute allowedRoles={['Vendor']}` + `VendorWorkspaceLayout` + `AccountModal`. Comment in source: “NOT AppLayout, parallel to the Client portal group.”

Nav in `VendorWorkspaceLayout`: `{Loan\|Title\|Your} Files · Documents · Tasks`. User chip: **Profile**, **Help Center** (new tab), **Log out**.

`AppLayout` explicitly bounces Vendor:

```1011:1013:src/layouts/AppLayout.tsx
  if (user.role === 'Vendor') {
    return <Navigate to={ROUTES.VENDOR_PORTAL} replace />
  }
```

`isAllowedForRole(..., 'Vendor')` only restores `/portal/vendor*`. Staff `/settings` is not a restorable vendor URL.

Login lands on `ROUTES.VENDOR_PORTAL` (`dashboardShellConfig` Vendor `landingRoute`). Public **Forgot password?** on `LoginPage` and `/reset-password` are shared auth, not staff chrome.

**This is enough to use the portal without the default workspace.**

### 2.2 The “Settings modal” is not Settings

`AccountModal` is the shared identity surface. Rail is role-switched in `railItemsForRole()`:

| Role | Account rail (as coded) |
| --- | --- |
| Internal (Agent / TC / Team Lead / Admin) | Profile, Notifications, My Checklist Templates, My Tagged Notes, My Preferred Vendors, My Internal Resources, Help & tour |
| FSBO | Profile, Notifications, Sharing, Security, Help & tour |
| Client | **Profile only** |
| **Vendor** | **Profile only** (same `case` as Client) |

The comment in `AccountModal.tsx` is explicit: Clients and Vendors “have no personal-preferences surface — identity (Profile) only,” because the old Client Preferences pane was FSBO/internal settings that “don’t apply to a represented client.” Vendors were grouped with Clients as a convenience, not because a mortgage partner has nothing to configure.

What Vendor Profile actually saves (`ProfileSection` + `PATCH /api/v1/users/me`):

- Photo, full name, **sign-in email**, phone, bio.
- **Not** email signature (hidden when `isPortal`).
- **Not** writing-style phrases (`WritingStyleCard` returns `null` for Client / FSBO / Vendor).

That is identity. It is not password, alerts, or help.

### 2.3 `/settings` is the staff hub — vendors never reach it

Default workspace Settings is `SettingsHubPage`, driven by `SETTINGS_CARDS` in `settingsCards.ts`. Groups:

- **Personal:** Profile, Notifications, Email & E-signature, Email Templates, My Playbook, Help & Tour.
- **Workspace:** Company, Branding, Billing, Users & Invites, Task Templates, Document Templates, Vendor Templates, Team Playbook, Integrations, AI & Automation, Payment Access, Advertising, Delete Organization.
- **Platform:** Platform Billing, Platform Advertising (`is_platform_admin`).

`SettingsRouter` says it will open the Account modal for “portal roles (Client / FSBO / Vendor).” That comment is **stale for Vendor**:

- `/settings` lives **inside** the `AppLayout` route tree.
- Vendor hitting `/settings` is bounced to `/portal/vendor` **before** `SettingsRouter` / `OpenAccountModalRoute` mounts.
- Client has `/client/settings` (opens Account over Home). FSBO has `/fsbo/settings`. **Vendor has no `/portal/vendor/settings`.**

Chip copy also differs: AppLayout says **Settings** and navigates to the hub; the vendor chip says **Profile** and `account.open('profile')`.

### 2.4 Notifications exist in config, not in the product

`dashboardShellConfig` Vendor: `notificationScope: 'vendor'`. That flag is unused on `VendorWorkspaceLayout` (no bell).

`GET /api/v1/notifications/pending` **returns empty buckets for Vendor on purpose** (same branch as Client / FSBO / Attorney) so portal roles never see staff task buckets or AI drafts.

`GET / PUT /api/v1/notifications/preferences` is authenticated for any user, but the matrix is **staff categories** (`task_assignment`, `ai_email_sent`, `daily_summary`, `milestone_share_viewed`, …). FSBO does **not** use that endpoint; it uses `/api/v1/fsbo/settings` with `project_prefs_for_fsbo()`. **There is no `/vendor-portal/settings` and no vendor category slice.**

### 2.5 Password already has an API; vendors have no in-portal control

- Public: `POST /api/v1/users/password-reset/request` (always 202) + `/forgot-password` + `/reset-password`.
- FSBO Account → Security calls the same request endpoint while signed in (`FsboSecurityPane`).
- Staff Settings hub **has no password card either** — agents also use Forgot password on login. Security in the Account rail is a **portal** pattern (FSBO), not a hub card.

A vendor who is already inside the portal has no “change password” affordance except logging out and using Forgot password.

### 2.6 Help is a staff website; tour cannot run on this shell

Vendor chip Help Center → `HELP_CENTER_URL` (`velvet-elves-help-center`). Seeded articles are **staff** (Vendor Directory, Vendor Templates, Vendor Proposals). There is no vendor-facing “how to use Loan Files / Documents / Tasks” article.

`HelpSection` calls `useTour()`. `TourProvider` wraps **AppLayout only**. The vendor `AccountModal` is **outside** that provider. Even if Help were added to the vendor rail today, **Start tour would throw** unless TourProvider is mounted on the vendor tree. `vendorSteps` still target staff `data-tour` hooks (`nav-documents`, `nav-uploads`, `topbar-notifications`) that the vendor shell does not render.

---

## 3 · Can it operate independently *today*?

### 3.1 Yes — job loop without the default workspace

A signed-in vendor can:

- Land on `/portal/vendor` after login.
- See assigned files, documents, tasks.
- Upload / request documents, mark tasks done, undo pending close-out, post a file note, edit profile, open Help Center in another tab, log out.
- Be kept out of staff URLs.

They do **not** need Company, Branding, Gmail, DocuSign, playbooks, Vendor Templates, or AI governance. Those belong to the brokerage.

### 3.2 No — not a finished standalone product

Without leaving the portal (or using tribal knowledge of `/forgot-password`), a vendor **cannot**:

| Need | Today |
| --- | --- |
| Change password from Account | Missing (FSBO has Security) |
| Choose email / in-app alerts | Missing (no vendor matrix, no bell) |
| Replay a tour of *this* UI | Missing (wrong steps + no TourProvider) |
| Bookmark “settings” | `/settings` bounce; no `/portal/vendor/settings` |
| Read partner-oriented help | Help Center is staff-written |
| Learn that a doc was shared or a close-out was sent back | No inbox; staff pending API is empty by design |

So: **independent enough to work a file; not independent enough to own an account.**

---

## 4 · Thoughts on copying default-workspace Settings

Agree with the instinct: **the vendor Account surface is too thin**, and the place to look for “what a VE user can configure” is Settings.

Disagree with cloning the hub.

### 4.1 Card-by-card: Settings hub → Vendor Account

**Personal group** (every internal role sees these tiles):

| Hub card | Copy into Vendor Portal? | Why |
| --- | --- | --- |
| Profile | **Yes — already there.** | Same `ProfileSection` / `PATCH /users/me`. Keep portal hide of signature + writing style. |
| Notifications | **Yes — adapted, not reused.** | Staff matrix includes AI email, teammate assignment, morning digest, share-link views. Vendors need assignment-to-file, document shared, request fulfilled, close-out approved/sent back, overdue *scoped* tasks. New feed + prefs; do not point the rail at `SettingsNotificationsPage`. |
| Email & E-signature | **No.** | Gmail / Outlook / DocuSign is how staff send mail. Vendors do not compose from VE. |
| Email Templates | **No.** | Staff-only allow-list in `settingsCards.ts`. |
| My Playbook | **No.** | Checklists, tagged notes, preferred vendors, internal PDFs are coordinator tools. “My Preferred Vendors” on the *staff* Account rail is agents picking inspectors — not a vendor picking themselves. |
| Help & Tour | **Yes — vendor copy.** | Help Center link already exists on the chip; it should also live in Account. Tour must be rewritten onto Files / Documents / Tasks and the shell must wrap `TourProvider`. |

**Workspace / Platform groups:** **never.** Company, seats, billing, users, task templates, **Vendor Templates** (staff outreach emails), Team Playbook, webhooks, AI thresholds, ads, delete-org. Putting any of this in the partner portal would leak the brokerage.

**Password:** not on the hub. Add it anyway, following **FSBO Security**, because portal users should not have to log out to rotate a password.

**Sharing:** FSBO-only (public milestone links). Vendors do not own listing share links. Omit.

### 4.2 Correct reference implementation

| Surface | Why it is / isn’t the template |
| --- | --- |
| `SettingsHubPage` | Inventory of *staff* configuration. Search + workspace tiles. Wrong IA for a partner. |
| Internal Account rail | Playbook sections vendors must not see. Notifications categories are staff. |
| **FSBO Account rail** | Right *shape*: Profile · Notifications · (skip Sharing) · Security · Help. Prefs go through a **portal-scoped** API, not `/notifications/preferences`. |
| Client Account rail | Wrong peer. Represented clients have no share surface and no partner-style alerts by product choice (`client_fsbo_settings.py` says Client settings were removed; “Clients now get Profile only … like Vendors”). That sentence documents the current coupling — it does not justify it for vendors. |

### 4.3 Do not re-open staff Settings for vendors

The 26 Aug bounce (`AppLayout` + `RoleRoute` + `returnLocation`) exists because vendors used to remount staff chrome. Re-allowing `/settings` would undo that. Keep the bounce. Grow the modal on the vendor tree.

---

## 5 · What “standalone” still needs (proposed Account)

Recommended vendor Account rail (same modal, more sections):

```
Profile          — keep
Notifications    — new vendor matrix + later a shell bell
Security         — reuse FsboSecurityPane pattern (email reset link), vendor copy
Help & tour      — Help Center + replay; vendor-specific copy and selectors
```

Chip: rename **Profile** → **Account** (or **Settings**) so it matches AppLayout language without routing to the hub. Optional: `/portal/vendor/settings` as `OpenAccountModalRoute` over Files home (mirror `/client/settings`), still inside `VendorWorkspaceLayout`.

### 5.1 Notifications — essential for standalone, not a Settings-hub paste

Until a vendor-scoped bell exists, the portal only works if the user **opens it**. Outside partners will not poll Files.

Ship:

- In-app list on the vendor shell (not `/notifications`).
- Prefs: email + in-app; no push; no `ai_email_sent` / `daily_summary` / `milestone_share_viewed`.
- Events: assigned to a file; document shared; request answered; close-out approved or sent back; overdue vendor-visible task (digest optional).
- Backend: empty staff `notifications/pending` stays empty; add vendor-portal notification APIs analogous to `/fsbo/settings`, not a widening of the staff pending payload.

### 5.2 Implementation constraints the hub does not have

These are why “just add the Settings cards” would fail if copied naively:

1. **TourProvider** is not on the vendor route tree. HelpSection’s Start tour requires it.
2. **`vendorSteps`** still describe Document Requests / My Uploads / topbar bell.
3. **Staff notification prefs API** would show a mortgage officer “AI email sent under your name.”
4. **Help Center content** is written for agents. A partner article (or a short in-modal primer) is needed or Help remains a wrong door.
5. **`SettingsRouter` vendor path is dead.** Any bookmark work belongs on `/portal/vendor/settings`, not `/settings`.

---

## 6 · What already makes the portal standalone (do not add)

Leave out of the vendor Account / shell:

- Workspace switcher (`WorkspaceSwitcher` is AppLayout-only — correct).
- Morning digest / `MorningDigestSection` (deal pipeline email).
- Connections, email templates, playbook, preferred-vendors picker.
- Staff Notifications page (`RoleRoute` internal + attorney).
- Ask Aime, calendar, payments, Client Messages tab.
- Visual restyle of the white vendor rail.

Daily work (files, documents, tasks) stays the product. Account is support chrome.

---

## 7 · Recommended finalize order (settings-shaped)

1. **Account rail = FSBO minus Sharing.** Profile (done), Security (reset email), Help (link + tour after TourProvider + rewritten steps).
2. **Vendor notification prefs + bell.** New API slice; do not reuse staff categories.
3. **`/portal/vendor/settings` bookmark** that opens the modal over Files; keep bouncing `/settings`.
4. **Partner Help Center article** (or in-modal short guide) so Help Center is not the staff Vendor Directory.
5. Unrelated to Settings but still required for a finished portal: date updates as Vendor Proposals (see `VENDOR_PORTAL_LOGIC_WORKFLOW_REVIEW_2026-08-26.md` L1).

Until 1–2 exist, the honest product line is: **“A scoped workspace you log into to check files,”** not **“A standalone partner application.”**

---

## 8 · Related code (for implementers)

| Topic | Where |
| --- | --- |
| Vendor rail = Profile only | `src/components/account/AccountModal.tsx` `railItemsForRole` |
| FSBO Notifications / Security | `src/components/account/sections/PortalSections.tsx` |
| Staff hub cards | `src/pages/settings/settingsCards.ts` |
| Vendor chip | `src/layouts/VendorWorkspaceLayout.tsx` `UserChip` |
| Staff bounce | `src/layouts/AppLayout.tsx` Vendor `Navigate` |
| Dead `/settings` claim | `src/pages/settings/SettingsRouter.tsx` comment vs AppLayout tree |
| Empty staff bell for Vendor | `app/api/v1/notifications.py` `get_pending_notifications` |
| FSBO prefs slice (pattern to copy) | `app/services/notification_prefs_service.py` `FSBO_*` + `app/api/v1/client_fsbo_settings.py` |
| Password request | `app/api/v1/users.py` `request_password_reset` |
| Tour not on vendor tree | `src/App.tsx` `TourProvider` only around `AppLayout` |
| Stale vendor tour | `src/components/tour/tourSteps.tsx` `vendorSteps` |

Earlier workflow review (logic bugs, date-update, Needs Attention): `VENDOR_PORTAL_LOGIC_WORKFLOW_REVIEW_2026-08-26.md`.
