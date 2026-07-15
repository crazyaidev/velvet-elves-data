# Google Approval: Who Resolves What

**Purpose:** the clean split of open issues between me (Jan) and Jake to get Google's approval for the Gmail connection. One line per issue, no filler.
**Written by:** Jan
**Date:** July 6, 2026
**Companion docs:** `GMAIL_GOOGLE_APPROVAL_PLAN.md` (the Jake-facing plan), `GMAIL_GOOGLE_APPROVAL_TODO.md` (my full working checklist), `GMAIL_GOOGLE_APPROVAL_GUIDELINES.md` (reference).

---

## My issues (Jan)

All preparation is mine: everything technical, all materials, and every guideline. Jake performs the final submission himself with the package I hand him (K5), so my last items produce that package instead of the submission click-through.

| # | Issue | Why it blocks approval | Status |
|---|---|---|---|
| J1 | Remove the unused `gmail.modify` permission from the code (`gmail_provider.py`) and retest connect, inbound sync, and send on staging | Asking for access the app never uses is Google's most common rejection reason; code-verified unused on 2026-07-06 | Code done 2026-07-06 (scope removed + guard comment, 46 email-integration tests green); staging OAuth retest pending |
| J2 | Decide whether the `profile` permission is really shown in the UI; drop it if not | Same minimum-access rule | Open |
| J3 | Verify the prod OAuth client redirect URIs (Gmail callback confirmed working 2026-07-06: Jake's flow reached the tester gate, which sits after redirect validation; Calendar callback still unverified), remove any dev URIs from the prod client | Broken sign-in return addresses fail the flow itself; dev leftovers fail review hygiene | Gmail leg done; verify Calendar + client hygiene in Console |
| J4 | Make the consent-screen scope list exactly match the trimmed code scopes | Code/Console mismatch is an automatic reviewer question | Open, after J1 |
| J5 | Complete consent-screen branding: app name, logo, home page, privacy and terms URLs, authorized domain `velvetelves.com` | Incomplete branding blocks submission | Open, support email needed from Jake (K2) |
| J6 | Verify `velvetelves.com` ownership in Google Search Console (I hold DNS in Route 53) | Unverified authorized domain blocks verification | Open |
| J7 | Write and publish the public pages: app privacy policy covering Gmail data, the exact Limited Use statement, AI disclosure, data deletion page, support page | Reviewers check public pages against the app; current `/legal` covers only the marketing email form | Open, needs K1 + K2 to finalize |
| J8 | Include the Calendar connection (`calendar.events`) in the submission | Calendar is a REQUIRED feature, not optional; it rides the same OAuth client, so it must be in the scope list, justifications, and demo video | Settled: include it (no owner sign-off needed) |
| J9 | Record and upload the unlisted demo video showing consent, inbound read, human-approved send, disconnect | Mandatory submission artifact | Open, after J1-J5 |
| J10 | Write the per-scope justifications | Mandatory submission artifact | Open |
| J11 | Prepare the security evidence packet (architecture, token encryption, tenant isolation, logging policy, AI provider no-training terms) | Expected for restricted Gmail read access; being ready avoids weeks of scramble if the audit round comes | Open |
| J12 | Build the submission package for Jake: a step-by-step guide for every Console screen (publish to Production, Verification Center), the exact paste-ready text for each question, page URLs, and the demo video link | Jake runs the submission (K5); the package must make it a half-hour walk-through of the guide with no decisions left open | Open, last before hand-off |
| J13 | Draft every reviewer answer within one business day of Jake forwarding a question; keep the question/answer log | Jake fronts the correspondence (K6) but the content is technical; slow replies are the most common self-inflicted delay | Standing rule once submitted |
| J14 | If Jake approves Workspace (K3): buy nothing myself, but migrate the project into the new organization before submitting | Ownership cleanup is far easier pre-submission | Waiting on K3 |
| J15 | Keep the tester list current meanwhile | Lets Jake's team keep testing during the whole process | Done for now: `jake@cbstiles.com` and `audri@cbstiles.com` added 2026-07-06 |

## Jake's issues

Six things, and only the first two block my work soon. K5 and K6 exist because Jake owns the submission: I provide materials and guidelines only.

| # | Issue | Why it is his | When I need it |
|---|---|---|---|
| K1 | Give me the company's legal name and state | Goes into the privacy policy and terms; it is a business fact, not a technical one | **DONE 2026-07-06**: Orange Door, LLP dba Velvet Elves, Indiana |
| K2 | Give me a support email address that a person actually reads, ideally `support@velvetelves.com` | Google requires a monitored support contact on the consent screen and public pages | **DONE 2026-07-06**: `support@velvetelves.com`; catchall now, real mailbox once Workspace lands. Monitoring is inherently the owners' (Jake/Audri handle company mail + review correspondence); no staff name needed from them |
| K3 | Buy Google Workspace for `velvetelves.com` (decision = YES, Jake started signup 2026-07-06) | It is a paid subscription on the company, and the project currently lives under his personal Google account | In progress: domain-verification record added by me 2026-07-07 (CNAME `73007731`→`google.com`, live + INSYNC); Jake clicks Verify / Check again in the signup to finish claiming the domain |
| K4 | During the review: change nothing inside the Google Cloud project | Unexpected changes can restart a review | From submission day until approval |
| K5 | Perform the submission in Google Cloud Console using my package (J12): publish to Production, walk the Verification Center screens, paste the prepared answers, attach the links, submit | He is the account under which the project lives and the owner of the submission; my package removes every technical decision from the walk-through | Same day the package lands if possible; package targeted for mid July (every idle day pushes launch a day) |
| K6 | Front the review correspondence: forward each reviewer email to me the same day, send back the answer I draft | Google writes to the submitter, which is him; I supply the content (J13), he supplies the same-day turnaround | From submission day until approval |
| K7 | If Google requires the paid security assessment (CASA): choose, engage, and pay an approved assessor | It is a paid engagement and a business decision, so it is the owners'. I advise on the approach and supply every technical material the assessor needs (J11); I do not engage or pay | Only if Google requires it |

Optional fifth: a read-through of the privacy policy text before it goes live (K1 makes it accurate; his sign-off makes it his).

## Not on either list

- The review duration itself: roughly 3 to 6 weeks after submission, up to ~8 with a security audit. Nobody can buy it down; the plan absorbs it by running in parallel with all other launch work.
- The possible security audit engagement and cost: only exists if Google demands the audit. If it happens, it is the owners' to engage and pay (K7); I advise on the approach and prepare the technical materials, and I never engage or commit spend myself.
- Team testing: not blocked by anything here; tester accounts work throughout.
