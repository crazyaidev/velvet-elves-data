# First Conference Release and Competitive Strategy — Proposal

**Prepared for:** Jake, Project Owner
**Prepared by:** Jan, Lead Developer
**Date:** August 12, 2026
**Subject:** Proposed release scope, competitive positioning against ListedKit, and delivery plan
**Release lock date:** September 12, 2026
**Conference:** September 22, 2026
**Status:** Awaiting approval; decisions required by August 18, 2026

---

## 1. Proposal Summary

I propose that Velvet Elves release the **complete implemented platform** at the First Conference, rather than a reduced feature subset.

A code-level review of the current backend and frontend confirms approximately **95 live product capabilities** spanning intake, task generation, deal management, automation, communication, portals, payments, and administration. This is materially broader than ListedKit's public product surface. The remaining work before September 22 is not core construction; it is **enablement, commercial configuration, and verification**.

The proposal has three components:

1. **Release the full implemented platform** (Section 4.1).
2. **Enable the seven items that are built but currently switched off or unconnected** (Section 4.2), including Morning Queue, founding price, and DocuSign.
3. **Exclude unbuilt capabilities from all conference claims** (Section 4.3), specifically SMS, native Follow Up Boss, and AI Coach.

Positioning statement for the conference:

> ListedKit is an AI transaction coordinator. Velvet Elves is the closing operating system — live today across intake, playbook, deal file, approvals, email, calendar, payments, and client, vendor, FSBO, and attorney portals.

---

## 2. Competitive Position: ListedKit

Assessed from ListedKit's public website on August 12, 2026.

### 2.1 Live capabilities

| Area | Public position |
| --- | --- |
| Contract and inbox reading | Any-state contracts; inbound email matched to deals |
| Timeline, tasks, pipeline | Generated from the contract; urgency across deals |
| Email automation | Drafts and scheduled reminders from Gmail/Outlook; human review before send |
| Calendar | Deadline sync to Google Calendar and Outlook |
| SMS | Text-based deal queries and instructions |
| Integrations | Gmail, Outlook, Follow Up Boss, Calendar |
| Ava Sign | Integrated e-signature; $29.99 per user per month after 30-day trial |
| Pricing | $14.99 per credit, reducing to $11.00 in bulk; first transaction free; no seat fees |

### 2.2 Not yet released

ListedKit's "Agentic Ava" capability set — overnight inbox monitoring, drafts prepared before the user asks, and unprompted party updates — remains **Coming Soon / waitlist** on their own product page.

### 2.3 Competitive assessment

| ListedKit advantage | Velvet Elves counter-position |
| --- | --- |
| Simpler single-loop product story | Demonstrate one complete closing file end to end |
| SMS and named Follow Up Boss integration | Exclude from claims; compete on platform depth |
| Lower headline price | Founding flat fee covering the full platform; first transaction free |
| Established public proof | Complete help content, dense demonstration data, accurate marketing |
| Agentic Ava marketing narrative | Release Morning Queue as a working, review-gated capability |

---

## 3. Current Implementation Status

Verified against source code; superseding any conflicting statements in earlier milestone documentation.

| Domain | Status |
| --- | --- |
| Authentication, RBAC (8 roles), multi-workspace, onboarding | Implemented |
| Role dashboards (Agent, Team Lead, Admin, Attorney, Client, FSBO, Vendor) | Implemented |
| Active Transactions pipeline, statuses, filters | Implemented |
| AI packet intake (multi-document parsing, citations, verification) | Implemented |
| Deterministic task generation, playbooks, templates, closing checklists | Implemented |
| Deal workspace (Overview, Timeline, Compliance, Tasks, Documents, Contacts, Billing, Activity, Email) | Implemented |
| Document management, versioning, requirements, compliance tracking | Implemented |
| Needs You approvals, automation postures, AI suggestions, deal agent | Implemented |
| Gmail and Outlook connection, inbound triage and deal matching, AI drafts, templates | Implemented |
| Closing calendar and Google/Outlook calendar push | Implemented |
| Client portal, FSBO workspace with public milestone sharing, Vendor portal | Implemented |
| Attorney matters, review queues, state rules, release workflow | Implemented |
| Invoicing and Stripe payment processing | Implemented |
| Audit logs, admin configuration, tenant branding, analytics, notifications, webhooks | Implemented |
| Marketing website, help centre platform, platform administration | Implemented |
| Overnight scheduler (Morning Queue) | Built; not enabled |
| Credit/flat-fee billing and founding price | Built; requires configuration |
| DocuSign | Built; production account not connected |
| SMS, voice, native Follow Up Boss, AI Coach | Not built |

---

## 4. Proposed Release Scope

### 4.1 Released at the conference

The full implemented platform as listed in Section 3, covering all eight roles, the intake and task engine, the deal workspace, automation and communication, all four external portals, the attorney workspace, payments, and administration.

### 4.2 Enablement required before September 12

| Item | Action required |
| --- | --- |
| Morning Queue | Enable scheduled sweep in staging, soak, then promote to production; overnight preparation only, no sending outside policy |
| Founding price and billing | Confirm flat-fee billing active; set founding fee; align application and marketing pricing |
| DocuSign | Connect a production or sandbox account (production currently points at the DocuSign demo host) and verify send and return-to-file |
| Automation postures | Confirm assisted and autopilot remain tenant opt-in, with review-first as the default |
| Help centre content | Load the authored article set into the live database |
| Demonstration data | Seed a representative brokerage account with healthy and at-risk transactions |
| Address type-ahead | Optional; requires a maps service key. Not required for release |

### 4.3 Excluded from all conference claims

SMS and voice channels; agent voice input; native Follow Up Boss and other named CRM adapters; AI Coach; the internal Sharing page; predictive and benchmarking analytics placeholders; web and mobile push notifications; FSBO self-serve signup; commission payouts (built but parked, with no live Stripe Connect account).

Marketing, presentation, and printed materials must be reconciled against Sections 4.1 and 4.3 before September 12.

---

## 5. Delivery Plan

Feature work concludes September 5. The period from September 6 to 12 is reserved for verification and defect resolution only.

| Phase | Dates | Scope |
| --- | --- | --- |
| 1. Release baseline | Aug 12–18 | Deploy outstanding intake and assistant fixes; seed demonstration account; verify all live paths on production; receive pricing decision |
| 2. Enablement | Aug 19–28 | Enable Morning Queue via staging soak and production promotion; confirm billing configuration at founding price |
| 3. Connection and publication | Aug 29–Sep 5 | Connect DocuSign; load help centre content; reconcile marketing claims; prepare portal demonstration accounts |
| 4. Verification and lock | Sep 6–12 | Complete live testing against Section 7; resolve blocking defects; lock release |

Following the lock date, the September 13–21 period is reserved for presentation rehearsal and conference logistics.

---

## 6. Conference Demonstration Plan

The primary demonstration is a five-minute sequence. It represents the demonstration path, not the limit of the released product.

1. Transaction pipeline with active deals
2. New transaction from a multi-document packet, showing citation and verification
3. Generated playbook tasks and timeline
4. Deal workspace: compliance and email
5. Needs You approval and send
6. Morning Queue

Secondary demonstrations, available on request: client, vendor, FSBO, and attorney portals; DocuSign; administration and audit; analytics; billing.

---

## 7. Release Readiness Criteria (September 12)

- Full implemented platform verified on production
- Morning Queue enabled, with no unapproved sends during soak
- Founding price live and consistent across application and marketing
- Flat-fee billing confirmed active
- Help centre article set loaded
- Marketing and presentation materials reconciled with Sections 4.1 and 4.3
- DocuSign connected and verified, or formally excluded from the demonstration
- Demonstration account restorable within fifteen minutes
- Portal and attorney demonstration accounts prepared
- Primary and secondary demonstration paths rehearsed

Any unmet criterion results in reduced claims rather than a change to the lock date.

---

## 8. Decisions Required by August 18

| # | Decision | Recommendation |
| --- | --- | --- |
| 1 | Founding price per transaction | $29.00, first transaction free (analysis floor: $25.00; current setting: $50.00) |
| 2 | Release scope | Approve full platform release per Section 4.1 |
| 3 | Claim exclusions | Approve Section 4.3, including SMS, Follow Up Boss, and AI Coach |
| 4 | DocuSign in the live demonstration | Include, subject to account provision by August 30 |
| 5 | Commission payouts | Remain parked until after the conference |

---

## 9. Post-Conference Roadmap

Sequenced according to conference feedback:

1. SMS channel
2. Native Follow Up Boss integration
3. Extended autonomous automation, retaining human approval as the default
4. Commission payouts and AI Coach, if commercialisation is approved

---

## 10. Risks

| Risk | Mitigation |
| --- | --- |
| Scope expansion into SMS or CRM integrations under competitive pressure | Section 4.3 approved in writing; feature freeze from September 5 |
| Morning Queue sending without approval | Staging soak, policy gating, review-first default |
| DocuSign account unavailable in time | Decision point September 1; exclude from demonstration if unresolved |
| Price comparison against a $14.99 headline | Founding price confirmed early; value framed against full platform scope |
| Demonstration data thin or unrepresentative | Seeded account with documented restore procedure |
