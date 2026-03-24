# Design File Feedback — Post Milestone 2.2

**Date:** 2026-03-23
**Reviewer:** Developer
**Context:** Milestone 2.2 (Task Engine Backend) is complete. Next: Milestone 2.3 (Frontend Foundation & Auth UI) and 2.4 (Transaction & Task UI). These designs are evaluated against the approved requirements, brandkit, style sheet, and system design.

---

## 1. VE - Active Transactions.html

**Overall:** Strongest design. Aligns most closely with the approved requirements in Section 2.6 (Agent/Elf Active Transactions Workspace).

### What works well

- Topbar with AI briefing chip + Critical / Needs Attention / On Track counters matches the spec exactly
- Dark sidebar with 2x2 KPI tiles (Overdue Tasks, Closing This Week, Active Deals, Pipeline Value) per requirements
- Sidebar navigation groups (Dashboard, Deals, Workflow, Intelligence) match the approved structure
- Transaction card pattern with left-edge urgency indicator, status pill, "why" badges, AI next-step banner, milestone bar, info badges — all per spec
- Three-column expanded drawer (Tasks, Key Dates, Contacts) matches requirements
- Filter tabs (All, Overdue, Due Today, Closing Soon, In Inspection, On Track, Unhealthy) with live counts
- Sort control with Urgency default
- Uses IBM Plex Sans + IBM Plex Mono correctly
- Color palette aligned: `--orange: #E26812`, `--sidebar-bg: #1E3356`

### Issues

- **Corner radius is 14px on cards, not the 6px specified in the style sheet.** The brandkit says "Use 6px radius for professional components. Do not drift into overly round consumer-app styling." This is a significant deviation.
- **Lora serif font is used** for transaction names (`.txn-name`) and page titles. The style sheet explicitly says: "do not bring serif typography into the application workspace." IBM Plex Sans should be used throughout.
- **Missing "Print Checklist" in expanded drawer footer** — the spec calls for footer actions: View/Add Transaction Documents, Print Checklist, Transaction History.
- **No inline search bar** visible next to sort control — the requirements specify an inline transaction search bar (next to sort control) for searching across client names, vendor names, companies, dates, addresses, and all transaction fields.
- **File size is 833KB** due to base64 encoded images — not a design issue but worth noting for handoff.

---

## 2. VE - Homepage Dashboard - Solo Agent.html

**Overall:** Homepage/Dashboard landing page. The requirements note this is "the next design phase" (Section 2.6 Dashboard). This design is ahead of the approved sequence but useful for planning.

### What works well

- "Start here" action queue with ranked interventions (Critical, Attention, At Risk) is exactly the "most important things today" briefing described in requirements
- Portfolio health score (68) with contextual explanation
- Pipeline snapshot with Pending GCI, Pending Volume, Closings YTD, Active Transactions
- AI portfolio intelligence cards with actionable suggestions
- Document drag-and-drop intake with AI explanation flow
- Floating "Ask Velvet Elves" AI assistant
- New Transaction modal with file handling and drag-and-drop support

### Issues

- **Lora serif font used** for headings (`--font-serif: 'Lora'`). Same violation as Active Transactions — no serif in the workspace per style sheet.
- **Corner radius is 18px** (`--radius: 18px`). Even further from the 6px spec.
- **Sidebar navigation differs from Active Transactions.** Solo Agent sidebar has flat nav (Home, Active Transactions, Documents, Tasks, etc.) instead of the approved grouped structure (Dashboard > Deals > Workflow > Intelligence). These must be consistent.
- **AI Coach upsell banners** appear twice (top and bottom of page). This is a monetization feature not in the current requirements. Is this approved scope or future? It takes significant page real estate.
- **No notification bell** in the topbar, unlike Active Transactions. Requirements specify notifications.
- **Color variables are slightly different** from Active Transactions (`--muted: #686868` vs `#7A7A7A`). These should be unified into one design system.

### Resolved — Completed Design

**Output file:** `completed_designs/ve-homepage_dashboard-solo_agent.html`
**Date:** 2026-03-24

All six issues above have been resolved in the completed design:

1. **Lora serif font removed.** All `font-family: var(--font-serif)` / `'Lora'` references eliminated. The Google Fonts import no longer loads Lora. Every heading, title, brand name, and deal name now uses IBM Plex Sans per the style sheet rule: "do not bring serif typography into the application workspace."
2. **Corner radius corrected to 6px.** All `border-radius` values changed from 14-22px to 6px across cards, buttons, panels, pills, inputs, modals, KPI tiles, and action items. Per brandkit: "Use 6px radius for professional components."
3. **Sidebar navigation unified with Active Transactions.** Replaced the flat nav (Home, Active Transactions, Documents, Tasks, AI Coach Upsell, Performance, Settings) with the canonical grouped structure: Dashboard (active), Deals (Active Transactions, Pending, Closed, All Transactions), Workflow (My Task Queue, All Documents, Closing Calendar), Intelligence (AI Suggestions, Analytics, Settings). Added 2x2 KPI tiles (Overdue Tasks, Closing This Week, Active Deals, Pipeline Value) and profile card at sidebar bottom, matching the Active Transactions design exactly.
4. **AI Coach upsell banners removed.** Both the top and bottom coach banners removed entirely. Not in current MVP requirements; scope needs confirmation from Jake before any implementation.
5. **Notification bell added to topbar.** Bell icon with notification pip now present in the topbar-right section, matching the Active Transactions topbar structure. Also added the "Today's AI Briefing" chip with Critical (3) / Needs Attention (5) / On Track (9) counters per Section 9.3.1.
6. **CSS variables unified with Active Transactions.** Color tokens, text colors (`--text-muted: #7A7A7A`, `--text-primary: #1A1A1A`, `--text-secondary: #4A4A4A`, `--text-ghost: #B0B0B0`), status colors, border values, and shadow values now match the Active Transactions design system. The `--font-serif` variable has been removed entirely.

Additional improvements applied:
- `font-variant-numeric: tabular-nums lining-nums` applied to all numeric display elements (KPI numbers, pipeline stats, countdowns, prices, dates, pills) per requirements Section 9.1.
- `min-height: 48px` / `min-width: 48px` applied to interactive targets (buttons, notification bell, close button, contact action buttons, form inputs) per WCAG AA / brandkit accessibility requirements.
- Topbar restructured to match Active Transactions: brand lockup on the left, AI briefing bar in the center, search + notification bell + user chip + New Transaction CTA on the right.
- Transaction card footers include "Print Checklist" action per the spec (Section 2.6e footer actions).
- Escape key closes modal and mobile sidebar (accessibility).
- Mobile responsive breakpoints with slide-out sidebar and overlay.

---

## 3. VE - Homepage Dashboard - Team Leader.html

**Overall:** Team leader variant of the dashboard. Matches the "Team Lead Active Transactions Workspace" concept but applied to the Dashboard landing page.

### What works well

- Team-scoped KPIs (Pending GCI, Pending Volume, Closings in 14 days, Team Health Score) with lifetime stats
- Intervention queue ranked by severity with close dates on every card — excellent
- "Why deals are drifting" panel gives actionable root-cause analysis
- Agent board with drill-down drawer showing per-agent KPIs, tasks, and jump actions
- Inline upload flyout on intervention cards (no navigation required)
- Pipeline health with stage distribution bars
- "What changed since last visit" badges in topbar — great UX pattern
- Contact bar in agent drawer for one-tap call/email/text
- Dynamic date in topbar
- Escape key closes drawer — good accessibility

### Issues

- **Lora serif font** again used for headings. Same style sheet violation.
- **Corner radius 18-20px** on panels. Same deviation from 6px spec.
- **AI Coach upsell** with a $79/agent/month pricing card is rendered in the design. Is this confirmed scope for MVP or a future feature placeholder? It should not drive implementation work right now.
- **Sidebar navigation structure** differs from both the Solo Agent and Active Transactions designs. Team Dashboard sidebar has: Team Dashboard, Active Transactions, Agents, Blocked Documents, AI Interventions, Communication Log, Production, AI Coach, Settings. This doesn't match the approved grouped structure (Dashboard > Deals > Workflow > Intelligence).
- **No AI Briefing chip in topbar** — the Active Transactions design has the "Today's AI Briefing" chip with Critical/Needs Attention/On Track counts. This should be consistent across all pages per Section 9.3.1.
- **"Coach prompt" terminology** — the requirements don't have an "AI Coach" product. This appears to be a new paid add-on. Scope needs clarification.

---

## 4. VE - Attorney Dashboard.html

**Overall:** Entirely new role/workspace concept not in the current requirements. The approved roles are: Agent, Elf, Team Lead, Admin, Client, Vendor. "Attorney" is not a defined role.

### Key observations

- Uses a **matter-centric sidebar** instead of deal-state navigation — sidebar lists individual matters (Rogers, Nguyen, Patel, Morris) rather than using the approved nav groups
- Has a **"Command Strip"** — a persistent next-action bar below the topbar showing the most urgent deadline with a direct CTA. This is a strong UX pattern worth considering for other views.
- Uses a **two-column workspace** (main content + right rail) with document rows, timeline, and AI brief card
- Sidebar shows stat pills: "3 need review today", "8 AI-prepared", "19 filed & clean"
- Matters have status badges: critical, attention, clean
- Brand mark shows ⚖️ (scales of justice) instead of the standard Velvet Elves icon

### Issues

- **This role doesn't exist in the requirements.** Is an Attorney role being added? If so, requirements and RBAC need updating. This has backend implications — Milestone 1.3 RBAC was already built for 6 roles.
- **Different layout paradigm** — no standard sidebar nav groups, no KPI tiles. If attorneys are a new role, they need to be specified in the requirements with permissions and access rules.
- **State-based task differences** (Section 4.11) mention attorney vs. title/escrow closing practices, but as task rules, not as a separate user role.
- **Font: IBM Plex Sans** is correctly used here (no serif violations in body — Lora is only on the matter name in topbar, which is minor).
- **Corner radius varies** (10px, 16px, 20px) — still not 6px per spec.

---

## 5. VE - FSBO Dashboard.html

**Overall:** For Sale By Owner (FSBO) dashboard — a consumer/seller-facing view. Most closely maps to the Client Portal (Section 1.7) but with a very different design language.

### Key observations

- **No sidebar** — uses a topbar-only layout with a centered max-width container. This makes sense for a consumer-facing portal.
- **Property tabs** at the top let the FSBO seller switch between their properties
- **"Next Step" card** with a clear CTA ("Respond to inspection issues") is excellent for non-technical users
- Summary cards: Missing Documents (with inline upload), Upcoming Deadlines (with consequences explained), Closing Timeline
- Timeline visualization showing transaction stages (done, active, pending states)
- Task list with contextual action buttons
- Contact cards for buyer, agent, title company, attorney
- "Velvet Elves Concierge" upsell strip at the bottom
- Deadline consequences pattern ("Missing this may allow the buyer to cancel the contract") — excellent, should be adopted across all views

### Issues

- **Completely different font stack:** Uses `DM Sans`, `Fraunces`, and `DM Mono` instead of IBM Plex Sans/Mono. The style sheet explicitly says IBM Plex Sans for the entire product UI. If this is a white-labeled/consumer-facing portal, maybe a different font is intentional — but it needs to be discussed and documented.
- **Different color palette:** `--orange: #D4621A` instead of `#E26812`. The background is `#F4F2EE` (warm) instead of `#F4F4F4` (cool gray per spec).
- **"FSBO" is not a defined concept in the requirements.** The Client role (Section 1.2e) covers buyers and sellers, but FSBO is specifically a seller without an agent. Does this represent the Client Portal? Or is this a new product direction?
- **Corner radii** are 10-28px, way beyond the 6px spec.
- **"Concierge" upsell** — another monetization feature not in current requirements. Same question: is this MVP scope?

---

## Cross-Cutting Issues

| Issue | Impact | Action Needed |
|---|---|---|
| **Serif fonts (Lora/Fraunces) in workspace** | Style sheet violation in 4 of 5 files | Confirm if style sheet rule has changed, or remove serif from all workspace typography |
| **Corner radius 14-28px instead of 6px** | Style sheet violation in all 5 files | Confirm if 6px rule still applies or has been officially updated |
| **Inconsistent sidebar navigation** across designs | Frontend architecture — can't build one nav component | Need one canonical nav structure for all authenticated views |
| **Two new "roles" (Attorney, FSBO)** not in requirements | Backend + RBAC impact (already built for 6 roles) | Confirm scope — are these MVP or post-launch? Update requirements if MVP. |
| **AI Coach / Concierge upsell** sections | Scope creep risk — appears in 3 designs | Confirm if these are MVP scope or placeholder designs for future |
| **Inconsistent CSS variables** across files | Design system fragmentation | Must be unified into one token set before implementation |
| **DM Sans font in FSBO** | Brand consistency break | Confirm if client portal intentionally uses a different font stack |
| **48x48px minimum interactive targets** | Accessibility (WCAG AA) requirement | Several buttons in the designs appear smaller than spec — needs QA pass |

---

## Recommended Implementation Approach

1. **Prioritize Active Transactions** — it's the most aligned with approved specs and maps directly to Milestone 2.4
2. **Unify the design system** — before building, get confirmation on one canonical set of CSS tokens (colors, radius, fonts, spacing)
3. **Clarify new scope** — Attorney Dashboard, FSBO Dashboard, and AI Coach are all new concepts not in the current requirements. Get written confirmation of scope before implementing
4. **Build Dashboard pages after Active Transactions** — per the milestone plan, Dashboard is "next design phase" (Milestone 5.1), so Solo Agent and Team Leader dashboards come later

---

## Questions for Jake

1. Has the 6px corner radius rule been updated? All designs use 14-28px.
2. Has the "no serif in the workspace" rule been updated? Lora is used for headings in 4 of 5 files.
3. Is the Attorney Dashboard a new role to add to RBAC, or a future concept?
4. Is the FSBO Dashboard the Client Portal, or a separate product direction?
5. Is the AI Coach ($79/agent/month) confirmed for MVP scope?
6. Is the Concierge upsell confirmed for MVP scope?
7. Which sidebar navigation structure is canonical — the grouped one from Active Transactions (Dashboard > Deals > Workflow > Intelligence) or the flat lists in the other designs?
8. Should the FSBO/Client portal use a different font (DM Sans) or stick with IBM Plex Sans?
