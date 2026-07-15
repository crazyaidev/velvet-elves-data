# Gmail + Calendar Google Approval: Materials to Prepare and Steps

**Purpose:** the concrete list of materials I (Jan) prepare for Google's OAuth verification, and the ordered steps to prepare them, ending at the package I hand to Jake.
**Prepared by:** Jan
**Date:** 2026-07-09
**Companion docs:** `GMAIL_GOOGLE_APPROVAL_STATUS_REPORT.md`, `GMAIL_GOOGLE_APPROVAL_TODO.md`, `GMAIL_GOOGLE_APPROVAL_RESPONSIBILITIES.md`, `GMAIL_GOOGLE_APPROVAL_GUIDELINES.md`

---

## The division (so this document's boundary is clear)

- **I (Jan, sole developer)** prepare every material and do the technical Google Cloud Console setup.
- **Jake and Audri (project owners, real-estate experts, non-technical)** perform the final submission using my package and front Google's review emails.
- This document therefore ends at "package ready, handed to Jake." What Jake does after that is summarized in Part C.

---

## Scope note (settled, not a decision)

Gmail and Google Calendar are **both required product features**, so the submission covers all of these on one OAuth client:

| Scope | Type | Feature |
|---|---|---|
| `openid`, `email`, `profile` | basic | account identity |
| `gmail.send` | sensitive | send user-approved replies |
| `gmail.readonly` | restricted | read inbound mail for matching + drafts |
| `calendar.events` | sensitive | write transaction deadlines to the user's calendar |

Calendar is not optional and needs no owner sign-off. It must appear in the consent-screen scope list, the scope justifications, and the demo video, exactly like Gmail.

---

## Part A: Materials checklist

| # | Material | What it is | Status (2026-07-09) |
|---|---|---|---|
| M1 | Final scope list | The four scopes above, matching the code | **Done** (code trimmed, `gmail.modify` removed) |
| M2 | Public pages | Home, privacy (with Limited Use), data deletion, terms, support contact | **Done, live** (see Appendix URLs) |
| M3 | OAuth client redirect URIs | Prod Gmail + Calendar callbacks correct, no dev URIs left in the prod client | To verify in Console |
| M4 | Consent-screen scope list | Console scopes set to exactly M1 | To do in Console |
| M5 | Consent-screen branding | App name, logo image, support email, developer contacts, home/privacy/terms URLs, authorized domain | To do (need the logo file) |
| M6 | Authorized-domain verification | `velvetelves.com` verified in Google Search Console for the consent screen | To do (add TXT the same way as the Workspace records) |
| M7 | Scope justifications | One concrete paragraph per sensitive/restricted scope: `gmail.send`, `gmail.readonly`, `calendar.events` | To do (text) |
| M8 | Demo video | Unlisted recording showing the OAuth grant and every scope in use, incl. Calendar | To do |
| M9 | Security evidence packet | The documents below (M9a-M9j) for the restricted-scope review / possible CASA | To do |
| M10 | Submission package for Jake | Step-by-step Console guide + paste-ready answers + links + video URL | To do (assembles M1-M9) |

**M9 security evidence packet contents:**

- M9a. Architecture diagram (browser, FastAPI backend, Supabase, Gmail API, Pub/Sub, Calendar API, AI provider, email provider).
- M9b. Data-flow diagram for connect, inbound sync, AI draft, send, calendar write, disconnect, deletion.
- M9c. Scope-to-API-method mapping (which Google endpoints each scope calls).
- M9d. Token storage design: encryption at rest, key location, rotation, access controls.
- M9e. PII encryption design (from `SYSTEM_DESIGN.md`).
- M9f. Multi-tenant isolation design + passing isolation tests (from `MULTI_TENANCY_IMPLEMENTATION_PLAN.md`).
- M9g. Logging policy proof: no tokens, auth codes, raw Pub/Sub JWTs, or full email bodies in logs; addresses masked.
- M9h. Vulnerability + dependency scanning process and evidence; criticals/highs remediated.
- M9i. Incident response plan (incl. notifying Google for any Google-data incident) + retention/deletion policy + backup encryption.
- M9j. Subprocessor list + AI-provider terms proving no training on our data.

If Google requires the paid security assessment (CASA), **engaging and paying an approved assessor is the owners' task (Jake/Audri), not mine.** My role stays what it is here: prepare M9a-M9j and advise on choosing an assessor. I do not engage or commit spend.

---

## Part B: Step-by-step preparation

Ordered. Steps 1 to 5 are technical Console/DNS work I do directly; steps 6 to 9 are the artifacts; step 10 is the handoff.

1. **Settle project ownership first (if migrating).** If Jake's Workspace completes and we move `velvet-vles` into the new organization, do it before anything below, because verification attaches to the project. If we are not migrating before submission, skip and proceed as-is.
2. **Fix the OAuth client (M3).** In the Console, confirm the prod redirect URIs are the two callbacks in the Appendix, and remove any dev/local redirect URIs from the prod client.
3. **Set the consent-screen scopes (M4).** Make the data-access scope list exactly M1: `gmail.send`, `gmail.readonly`, `calendar.events` (plus openid/email/profile). No `gmail.modify`.
4. **Complete consent-screen branding (M5).** App name "Velvet Elves", the production logo image, support email `support@velvetelves.com`, developer contact emails, home `https://velvetelves.com/`, privacy `https://velvetelves.com/privacy`, terms `https://velvetelves.com/legal`, authorized domain `velvetelves.com`.
5. **Verify the authorized domain (M6).** Add the Search Console verification TXT in Route 53 (same method used for the Workspace records) and confirm it in Search Console.
6. **Write the scope justifications (M7).** One tight paragraph each, feature-specific, naming the API methods and the on-screen feature, for `gmail.send`, `gmail.readonly`, and `calendar.events`. Emphasize human approval before any send.
7. **Record the demo video (M8).** Dedicated test Google account, seeded test transaction, no real client data. Show, in order: the public home + privacy pages, sign-in, Settings > Integrations, the full OAuth consent screen with permissions visible, connected state, an inbound email landing on the deal, an AI draft (state clearly the AI does not send), Approve & Send, the sent message, a Calendar event being written, then Disconnect. Upload as unlisted, keep the link.
8. **Assemble the security evidence packet (M9).** Produce M9a-M9j into one folder. Most of the content already exists in the codebase and design docs; this step is drawing the two diagrams and writing the short policy statements.
9. **Correct the "renews daily" wording** in the guidelines/security answers to the real mechanism (renew-after-sync in the webhook + the `renew-due` scan endpoint) so M9 and M7 match what the code actually does.
10. **Assemble the submission package for Jake (M10).** A single guide: the exact Console screens to click (publish to Production, open Verification Center), the paste-ready scope justifications, the documentation links (home, privacy, data deletion), and the unlisted video URL, with nothing left for Jake to decide.

Note on "publish to Production": the app is currently in Testing (tester allowlist). Publishing to Production, done as part of the submission, also ends the roughly weekly token expiry that keeps disconnecting testers.

---

## Part C: What Jake does with the package (for context, not my prep)

1. In the Console, publish the app to Production.
2. Open the Verification Center and start verification.
3. Paste the prepared scope justifications and add the documentation links and the video URL.
4. Submit.
5. During review, forward each Google email to me the same day; I draft the answer, he sends it. Change nothing in the Cloud project while the review runs.

---

## Appendix: paste-ready facts

- **GCP project:** Velvet Elves, `velvet-vles` (538509143953)
- **Scopes:** `openid`, `email`, `profile`, `https://www.googleapis.com/auth/gmail.send`, `https://www.googleapis.com/auth/gmail.readonly`, `https://www.googleapis.com/auth/calendar.events`
- **Prod redirect URIs:**
  - `https://api.prod.velvetelves.com/api/v1/integrations/gmail/callback`
  - `https://api.prod.velvetelves.com/api/v1/calendar/google/callback`
- **Public URLs (live):**
  - Home `https://velvetelves.com/`
  - Privacy `https://velvetelves.com/privacy`
  - Data deletion `https://velvetelves.com/data-deletion`
  - Terms `https://velvetelves.com/legal`
  - Support `support@velvetelves.com`
- **Authorized domain:** `velvetelves.com`
- **Limited Use statement (already on the privacy page):** "Velvet Elves' use and transfer of information received from Google APIs to any other app will adhere to the Google API Services User Data Policy, including the Limited Use requirements."
