# Marketing Site: Comprehensive Feature Coverage + Accurate Screenshot Plan

**For:** Jake's sign-off (before I capture screenshots or build pages)
**Date:** 2026-06-29
**Author:** Jan
**Scope:** Make the marketing site present ALL key product features, each paired with a screenshot that actually shows that feature. This doc is the inventory + proposed structure + the exact screenshot capture map. No code or captures yet.

---

## 1. Why this is needed

The current site presents only a sliver of the product (two "elves" + a three-step story) and reuses three screenshots that often do not match the copy. The product is far larger. Below is the real feature set (grounded in the actual frontend routes in `velvet-elves-frontend/src/App.tsx` and the in-app sidebar taxonomy), then a proposed site structure that covers it, then a screenshot plan that guarantees each image matches its feature.

---

## 2. Feature inventory (grounded in the real app)

Legend: **LIVE** = shipped and shootable today · **SOON** = present but gated/teaser/stub, must be labeled "coming soon" · **INTERNAL** = platform/admin, not marketing-facing.

### Pillar A — Transactions (the core loop)
| Feature | App route | Status |
| --- | --- | --- |
| AI New-Transaction Intake (Wizard): drop/forward the contract, AI extracts parties, property, price, and every date | `/transactions/new` | LIVE |
| Transaction Workspace + conversational AI agent: timeline, tasks, documents, email, "Velvet suggests," mismatch-resolve | `/transactions/:id` | LIVE |
| Pipeline / Active Transactions (table, statuses: active/pending/closed/all) | `/transactions/active` | LIVE |
| Clients hub (cross-deal index of represented clients) | `/clients` | LIVE |

### Pillar B — Tasks & deadlines
| My Task Queue (deadline-aware task list, severity, follow-ups) | `/tasks` | LIVE |
| Task Templates + My/Team Playbook (standardized workflows) | `/admin/templates`, `/settings/my-playbook` | LIVE |

### Pillar C — Documents
| All Documents (checklist, Missing Docs, priority events, "cleared today" ledger) | `/documents` | LIVE |
| E-signature send (Send for Signature / DocuSign) | within `/documents` | LIVE |
| Document Template Library (upload fillable PDFs, map fields once, auto-fill + flatten) | `/settings/document-templates` | LIVE |

### Pillar D — Email & AI communication
| AI Email Review (AI drafts replies, approval-before-send) | `/ai-emails` | LIVE |
| Email Templates | `/email-templates` | LIVE |
| Autopilot / auto-emailing (send cadences) | flag-gated | SOON |
| Voice Elf, SMS Elf | backend stubs | SOON |

### Pillar E — Calendar
| Closing Calendar (key dates, deadlines, recording dates) | `/calendar` | LIVE |

### Pillar F — Vendors
| Vendor Directory (table + detail modal) | `/vendors` | LIVE |
| Vendor Proposals (inbound proposals, reject→counter-offer) | `/vendor-proposals` | LIVE |
| Vendor Portal (vendor-facing files, tasks, documents) | `/portal/vendor` | LIVE |

### Pillar G — Payments
| Invoices & Payments (create, send, pay links) | `/payments` | LIVE |
| Commission Payouts | `/payments/payouts` | LIVE |
| Public invoice pay page (no login) | `/pay/invoices/:id` | LIVE |

### Pillar H — Intelligence & analytics
| AI Suggestions | `/ai-suggestions` | LIVE |
| Analytics (pipeline, per-user/team reports, charts) | `/analytics` | LIVE |
| AI Coach | Team-Lead teaser | SOON (locked teaser) |

### Pillar I — Client experience
| Client Portal "closing concierge" (Home, Next Steps, Updates, Documents, Milestones, Timeline, Agent info, Invoices) | `/client` | LIVE |
| Public milestone viewer / share links | `/milestones/:shareToken` | LIVE |

### Pillar J — Role workspaces (audience dashboards)
| Solo Agent dashboard | `/dashboard/agent` | LIVE |
| Team Leader dashboard | `/dashboard/team` | LIVE |
| Attorney Workspace (Matters, Releases queue, Recording calendar, State rules) | `/transactions/:id` (attorney), `/attorney/*` | LIVE |
| FSBO Workspace (Overview, Properties, Documents, Milestones) | `/fsbo` | LIVE |

### Pillar K — Trust, team & oversight
| Team Overview (pipeline across the team) | `/team` | LIVE |
| Teams + Team Settings (checklist/notes/vendors/resources) | `/admin/teams`, `/admin/team-settings` | LIVE |
| Users & role-based access | `/admin/users` | LIVE |
| Communication Audit | `/admin/communications` | LIVE |
| Audit Log | `/admin/audit-logs` | LIVE |
| AI Governance (provider selection, confidence) | `/admin/confidence` | LIVE |
| Integrations (Gmail, calendar, e-sign) | `/admin/integrations` | LIVE |

### Pillar L — Platform / white-label (mostly NOT marketing-facing)
Multi-tenant Tenants, Platform AI usage, Platform billing, Advertising storefront, Help Center authoring. **Proposed: exclude** from the feature marketing (these run Velvet Elves itself), except a light "white-label / your brand" mention under Trust.

---

## 3. Proposed marketing site structure

Two options for HOW to present the full set. I recommend Option 1 now; Option 2 can follow.

### Option 1 (recommended) — One comprehensive `/features` showcase
- Rebuild `/product` into a tight **overview** (the platform in one screen: the loop + the pillars) that links into `/features`.
- New **`/features`** page: every pillar above as its own section, each an alternating screenshot + copy band with the feature's **own accurate screenshot**, grouped under headers (Transactions · Tasks · Documents · Email & AI · Calendar · Vendors · Payments · Intelligence · Client experience · Trust & oversight). Coming-soon items appear clearly labeled, without screenshots.
- Keep the audience pages (`/agents`, `/brokers-teams`, `/fsbo`, `/attorneys`, `/client-portal`); each keeps its hero + a curated subset of the relevant feature bands (reusing the same accurate screenshots).
- Add "Features" to the top-bar **Product** dropdown and the footer.

**Pros:** comprehensive, one strong scroll, fastest to ship, every screenshot in one capture pass. **Cons:** long page (mitigated by a sticky in-page section nav).

### Option 2 (later) — Feature hub + per-category deep pages
A `/features` grid hub linking to `/features/<category>` deep-dive pages (more SEO surface, more pages to design/maintain). I suggest doing Option 1 first, then promoting the highest-traffic categories into deep pages.

**Decision needed (Q1):** Option 1 now, or go straight to Option 2?

---

## 4. Screenshot capture plan (the accuracy guarantee)

### 4.1 Method
Re-add the documented throwaway MSW browser harness to `velvet-elves-frontend` (bootstrap in `main.tsx` gated on `VITE_USE_MSW`, reusing `src/tests/mocks/handlers.ts`), seed realistic mock data with the personas below, run `VITE_USE_MSW=1 vite`, and capture each route via Chrome DevTools at 1440×900 @2x. **The harness is reverted afterward** so the app is unchanged. Each image is named for its feature and dropped into `velvet-elves-marketing-new/public/screens/`.

### 4.2 Personas (realistic American names; agent = your requirement)
- **Agent / Team Lead:** **Sarah Mitchell** (the account name in the sidebar chip, "assigned to," AI greeting, signatures, everywhere the logged-in user shows). Replaces "Test Agent" everywhere.
- **Client (buyer):** Jordan Avery
- **FSBO seller:** Daniel Brooks
- **Attorney:** Karen Whitfield, Esq.
- **Vendor:** Coastal Title & Escrow (contact: Maria Lopez)
- **Sample deal:** 1428 Magnolia Ave (buyer Jordan Avery, seller the Delgado family) — consistent across screens so the story hangs together.

**Decision needed (Q2):** confirm "Sarah Mitchell" (and the supporting names), or give me your preferred set.

### 4.3 Exact capture map (one accurate screenshot per feature)
| # | Marketing section | Screenshot file | App route captured | Persona/role |
| --- | --- | --- | --- | --- |
| 1 | AI intake wizard | `screen-wizard.png` (refresh) | `/transactions/new` | Sarah Mitchell (Agent) |
| 2 | Transaction workspace + AI agent | `screen-workspace.png` | `/transactions/:id` | Agent |
| 3 | Pipeline / active transactions | `screen-transactions.png` (refresh) | `/transactions/active` | Agent |
| 4 | My Task Queue | `screen-tasks.png` | `/tasks` | Agent |
| 5 | All Documents | `screen-documents.png` | `/documents` | Agent |
| 6 | Document Template Library | `screen-doc-templates.png` | `/settings/document-templates` | Admin (Sarah) |
| 7 | AI Email Review | `screen-email.png` | `/ai-emails` | Agent |
| 8 | Closing Calendar | `screen-calendar.png` | `/calendar` | Agent |
| 9 | Vendor Directory | `screen-vendors.png` | `/vendors` | Agent |
| 10 | Vendor Proposals | `screen-vendor-proposals.png` | `/vendor-proposals` | Agent |
| 11 | Invoices & Payments | `screen-payments.png` | `/payments` | Agent |
| 12 | AI Suggestions | `screen-ai-suggestions.png` | `/ai-suggestions` | Agent |
| 13 | Analytics | `screen-analytics.png` | `/analytics` | Agent |
| 14 | Team Overview | `screen-team.png` | `/team` | Sarah Mitchell (TeamLead) |
| 15 | Communication Audit / Audit Log | `screen-oversight.png` | `/admin/communications` | TeamLead/Admin |
| 16 | Client Portal | `screen-client-portal.png` | `/client` | Jordan Avery (Client) |
| 17 | Attorney Workspace | `screen-attorney.png` (keep/refresh) | `/transactions/:id` (attorney) | Karen Whitfield |
| 18 | FSBO Workspace | `screen-fsbo.png` | `/fsbo` | Daniel Brooks |
| 19 | Vendor Portal | `screen-vendor-portal.png` | `/portal/vendor` | Coastal Title |
| 20 | Solo Agent dashboard | `screen-dashboard.png` | `/dashboard/agent` | Agent |

Coming-soon items (Voice, SMS, Autopilot, AI Coach) get **no screenshot** — they are shown as labeled "coming soon" cards, consistent with today's honesty rule.

### 4.4 Accuracy guarantee
Every marketing band uses only the file captured from that exact route, and the `alt` text describes what that screen actually shows. No image is reused across unrelated features. The three current screenshots are either re-captured fresh (wizard, transactions, attorney) or replaced.

---

## 5. Honesty rules carried forward
- Only LIVE features are shown as available; SOON features are labeled "coming soon" with no screenshot.
- No invented metrics, testimonials, or logos.
- Product claims match the implementation (I will re-verify the deadline/task-generation claim against the current engine before stating it as automatic — see prior plan §5.4).

---

## 6. Sign-off checklist
- **Q1 — Structure:** Option 1 (one comprehensive `/features` page now) ✅ recommended, or Option 2 (hub + deep pages)?
- **Q2 — Personas:** confirm Sarah Mitchell (agent) + the supporting names, or supply your own.
- **Q3 — Scope of pillars:** include all of A–K? Exclude platform/white-label (L) as proposed?
- **Q4 — Capture permission (D-7):** OK for me to briefly run the frontend with the MSW harness to capture the 20 screens, then revert it?
- **Q5 — Coming-soon items:** confirm Voice, SMS, Autopilot, AI Coach stay "coming soon" (no screenshot).

On your sign-off I will: capture the 20 screenshots with the personas, build the comprehensive `/features` page (Option 1) + overview + audience-page wiring, and verify with a full build + screenshots.
