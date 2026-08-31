# Vendor Portal — is staff AI automation needed inside the portal? (2026-08-26)

**Status:** Analysis only. No source was changed.  
**Question:** AI automation runs in the default (staff) workspace. Does the Vendor Portal also need that functionality? The portal currently feels too limited.  
**Method:** Live frontend and backend, not data-folder plans alone. Plans used only where they record Jake’s words.

---

## 0 · Accurate answer

**No. The staff AI automation suite should not be copied into the Vendor Portal.**

Aime, Needs You, Autopilot, AI Emails, overnight sweeps, contract intake, confidence gates, and Settings → AI & Automation are tools for people who **run the deal**. A Vendor is a scoped third party. Those surfaces would leak the pipeline the portal was built to hide.

**Yes, one specific AI job already belongs in the vendor *workflow* — and it is already implemented on the server, not as a vendor console:**

Jake asked that when a mortgage/title partner marks a task done (upload or comment), **AI judges whether the work is actually complete and may close the task.** That is `verify_task_completion` on `POST /vendor-portal/tasks/{id}/completion-request`. The **switch lives in the staff workspace** (`VendorAutoCloseSettingsCard` on Vendor Templates). Default **off** (J3). The vendor should see the **result** (In review / Closed / Sent back), not Manual vs Autopilot.

**The portal feels limited for a different reason.** It is missing partner-product pieces (notifications, honest date updates, Account, tour, Needs Attention). Those gaps are real. They are not fixed by giving a loan officer Aime.

| Claim | Verdict |
| --- | --- |
| Vendors need the same AI automation **screens** as Agent/TC | **False.** APIs are `require_role` Agent / TC / Team Lead / Admin. Vendor is excluded on purpose. |
| Vendors need AI to **do their job faster** | **Partly true** — as a **judge behind close-out** (and email date-parse on the staff/email side), not as a vendor Autopilot. |
| The portal is too limited | **True** — vs a finished partner app. **False** — if “limited” means “missing Aime / Email / Needs You.” |
| Turning on AI auto-close inside the portal settings | **Wrong place.** Tenant policy; Admin/TC already have the toggle. |

---

## 1 · What “AI automation” actually is in the default workspace

These are live staff features (feature list Part A + routers). None of them are mounted on `VendorWorkspaceLayout`.

| Staff surface | What it does | Who may call the API |
| --- | --- | --- |
| Settings → **AI & Automation** | Tenant posture Manual / Assisted / Autopilot, model, overnight health | Team Lead / Admin (`/automation/settings`) |
| **Needs You** | Residual queue: ready to send, AI proposal, draft, decision | Agent / TC / TL / Admin |
| **Email** (`/ai-emails`) | Inbox/outbox; Aime drafts; human send | Internal |
| **Autopilot letters** | Named welcome / title-order / inspection-reminder may auto-send when confidence is high | Admin policy; wire/legal never auto-send |
| **+ New Transaction** wizard | AI parse of the contract packet; task plan from templates + confirmed dates | Internal |
| **Aime** (Ask Aime / ✦ Ask AI FAB) | Deal Q&A, proposed actions awaiting approval | Staff pages + Attorney + FSBO shell — **not** vendor routes |
| **AI Suggestions** | Next-best actions on deals | Internal |
| Overnight scheduler | Hourly tick; health chip | Admin |
| Task **automation_level** | Manual vs Automated on checklist items | Internal |

`app/api/v1/automation.py` `_WORKSPACE_ROLES` = Agent, TransactionCoordinator, TeamLead, Admin. **Vendor is not in the list.** A vendor hitting `/automation/*` is 403 even if the UI were pasted in.

`AskAiFab` is rendered on staff pages (Active Transactions, Task Queue, All Documents, Needs You) and Attorney. `AiChatProvider` wraps **AppLayout**, not the vendor tree. Vendors are bounced off AppLayout. They have **no Ask AI button today**, by routing, not by accident.

That is the correct isolation: automation is “how Velvet Elves runs the brokerage’s file,” not “how a title company uses a portal.”

---

## 2 · AI that already exists *for* vendors (mostly not in the portal)

The product is already AI-involved in vendor work. Almost all of it is **staff- or email-side**.

### 2.1 Email reply → date proposal (staff + mailbox)

Inbound vendor mail is parsed; `VendorProposalService.propose_from_vendor_reply` creates a `vendor_proposals` row. Coordinators accept/reject on **Intelligence → Vendor Proposals**. Deadlines never move themselves. This is the same doctrine as Autopilot: **AI proposes, human (or policy) decides.**

The vendor does not need an Email workspace for this. They reply in their own inbox, or (once Phase A of the finalize plan ships) they submit a date **in the portal**, which should create the same proposal type with `origin=portal`.

### 2.2 Vendor Templates (staff)

Constrained outreach (“Reply with: Scheduled: YYYY-MM-DD”). The AI can send those from the **staff** deal. Settings → Vendor Templates. Not a vendor-portal feature.

### 2.3 Close-out verifier (runs on the portal API, judged for staff policy)

On vendor `completion-request`:

1. Row in `vendor_task_actions`, status `pending`.
2. If tenant `settings_json.vendor_comms.ai_autoclose_enabled` is **false** (default): **no model call**; human queue (`VendorTaskReviewQueue`).
3. If **true**: `verify_task_completion` (tenant’s **manually selected** provider, never auto-switched). Confident `complete` → task closed, status `auto_completed`. Otherwise pending. Provider failure → pending, never silent close.

The portal UI already knows how to show **Closed by AI · N%** (`VendorPortalTasksPage` `StatusChip`). Tests exist (`test_ai_autocloses_when_enabled_and_confident`). Admins turn it on in **staff** `VendorAutoCloseSettingsCard`.

So: **AI automation for vendors is already designed. It is a backend judge + a staff toggle, not a second Autopilot page.**

### 2.4 Copy that oversells AI in the portal

`_project_task` hardcodes `requested_by="Velvet AI or your coordinator"`. Tasks page body says close-outs are “routed to Velvet AI or your coordinator.” With auto-close **off**, that is inaccurate. Honest vendor copy is “your coordinator” until the tenant enables auto-close. That is a wording fix, not a reason to add Aime.

---

## 3 · What Jake actually required

From `VENDOR_WORKSPACE_SUPERIOR_PLAN.md` §1.2 (Jake’s notes):

- Easy to navigate; **mortgage- or title-scoped** tasks and docs.
- Doc center: shared docs + **request** what’s missing.
- Close-out by **upload or comment**; **“AI then determines whether the task was truly completed and closes it.”**
- Contacts: own section only; mortgage never sees seller.

He did **not** ask for: Ask Aime, Needs You, AI Emails, Autopilot posture, contract wizard, writing style, Gmail, morning digest, or a vendor Settings → AI & Automation.

Open question **J3** is whether AI may close outright or only recommend. Code took the safe default: **recommend only**, Admin may opt in. That decision stays with the brokerage, not the partner.

FSBO gets Ask AI because they **own the listing** and have no agent OS. Clients get **Ask your team** (a thread), not the staff Aime agent. Vendors are closer to an **outside processor** than to either of those. A third chat (Aime) on top of file notes + email would compete with the coordinator, not replace missing notifications.

---

## 4 · Why copying staff automation would make the portal worse

1. **Scope wall.** Automation queues are cross-deal, tenant-wide, and include AI drafts “under your name.” A vendor user_id on those APIs would be a leak even with UI filtering. The empty `GET /notifications/pending` for Vendor exists for the same reason.

2. **Wrong operator.** Autopilot sends **title-order and inspection-reminder** letters. The vendor is often the *recipient* of that mail, not the sender. Putting send policy in their Account would be incoherent.

3. **Deadlines.** Staff rule: deadlines never move themselves. Portal date updates must be **proposals**. An in-portal Aime that “updates the appraisal date” would violate that.

4. **Job, not OS.** A loan officer’s job in VE is: see my files, upload, request, mark done, confirm dates. Three nav items match that. Adding Intelligence / Email / Needs You turns the portal back into a thin staff app — the failure mode the dedicated shell was meant to end.

5. **Cost and liability.** `verify_task_completion` already bills the tenant’s provider when auto-close is on. A chatty Aime on every vendor session would spend tokens on people who cannot act on most answers.

---

## 5 · The portal is limited — but not because Aime is missing

Compared to a **finished partner product**, yes, it is thin. The missing pieces (already listed in the logic and Account reviews) are:

- Date submit is a note, not a proposal.
- No vendor bell / email prefs.
- Account is Profile-only (no password, no Help rail that works).
- Tour still describes staff chrome.
- Needs Attention and helper cards are incomplete.
- Notes/requests do not ping the coordinator in-app.

Compared to **staff VE**, it is *supposed* to be smaller: Files, Documents, Tasks, Account. That is Jake’s Mortgage Partner Portal, not a cut-down Transaction OS.

If the goal is “feel as capable as the default workspace,” the wrong move is to import automation chrome. The right move is to finish the partner loop so the vendor never needs to log into staff VE (they cannot anyway) and never wonder whether anyone saw their upload.

---

## 6 · What AI *should* do for vendors (precise)

### Keep / finish (belongs)

| Item | Where it lives | Vendor sees |
| --- | --- | --- |
| Close-out verifier | Portal API + staff toggle | In review / Closed by AI / Sent back + reason |
| Email date parse | Staff Email + Vendor Proposals | Optional: later, “your date is in review” in the bell |
| Portal date → same proposal queue | Not built yet (finalize Phase A) | Toast: sent for coordinator review |
| Honest incomplete feedback | Partially: `action_reason` on reject; AI reasoning stored on the action | If auto-close on and verdict incomplete: **plain-language “still needed”** on the task (plan §8.2). Worth adding when J3 is on. Not a new nav item. |

### Do not add to the vendor shell

- Ask Aime / Ask AI FAB / `AiChatProvider` on `/portal/vendor*`
- Needs You, `/automation/*`, Autopilot, overnight health
- AI Emails inbox, writing style, mailbox connect
- AI Suggestions, Analytics, contract wizard
- Vendor-facing confidence sliders or model picker
- Client-style “Ask Velvet” as a fourth inbox (file note already exists)

### Optional later (only if Jake asks)

- **Computed “next step”** is already non-LLM (`_next_step` from scoped tasks). Keep it rule-based.
- A single **“What is this task asking for?”** explainer using the task description already on the card — not a chat.
- Enable auto-close for a tenant **in staff settings**, then show Closed by AI + one-sentence reason on expand. That *is* Jake’s AI in the portal, without an automation product.

---

## 7 · Recommendation

Treat AI for vendors as **invisible infrastructure with visible outcomes**:

1. Do **not** port default-workspace AI automation into the Vendor Portal.
2. Do **finish** the partner product (notifications, date proposals, Account, honest copy). That is what makes the portal feel complete.
3. Keep **J3 auto-close** as a **brokerage** switch. When off, stop promising Velvet AI in vendor copy. When on, show Closed by AI and incomplete reasoning on the task — still no Autopilot UI.
4. Staff continues to own Aime, Email, Needs You, and Vendor Proposals. Those *are* the AI automation layer for vendor work; the portal is the intake surface.

Until (2) ships, the accurate product line is: a **scoped workspace**, not an underpowered copy of Transaction OS, and not “AI-first” on the partner side except as a close-out judge.

---

## 8 · Source map

| Topic | Where |
| --- | --- |
| Automation roles | `app/api/v1/automation.py` `_WORKSPACE_ROLES` |
| Close-out + auto-close | `app/api/v1/vendor_workspace.py` `request_task_completion`, `_vendor_autoclose_policy` |
| Verifier | `app/services/vendor_task_verifier.py` |
| Staff toggle | `src/components/vendors/VendorAutoCloseSettingsCard.tsx` |
| Closed by AI chip | `src/pages/vendor/VendorPortalTasksPage.tsx` `StatusChip` |
| Overselling copy | `_project_task` `requested_by`; Tasks page intro |
| Ask AI not on vendor | `AskAiFab` usages; `App.tsx` vendor group has no `AiChatProvider` |
| Jake close-out AI | `VENDOR_WORKSPACE_SUPERIOR_PLAN.md` §1.2, §8.2, J3 |
| Staff AI inventory | `VELVET_ELVES_CURRENT_FEATURE_LIST_2026-08-25.md` §§4–13, 18 |

Related: `VENDOR_PORTAL_LOGIC_WORKFLOW_REVIEW_2026-08-26.md` (L10), `VENDOR_PORTAL_STANDALONE_SETTINGS_REVIEW_2026-08-26.md`, `VENDOR_PORTAL_FINALIZE_IMPLEMENTATION_PLAN_2026-08-26.md`.
