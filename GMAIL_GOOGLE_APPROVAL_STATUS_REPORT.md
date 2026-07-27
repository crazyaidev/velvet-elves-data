# Gmail + Calendar Google Approval: Status Report

**As of:** 2026-07-23 (supersedes the 2026-07-09 revision)
**Prepared by:** Jan
**Companion docs:** `GMAIL_GOOGLE_APPROVAL_MATERIALS_AND_STEPS.md` (materials + prep steps), `GMAIL_GOOGLE_APPROVAL_TODO.md` (working checklist), `GMAIL_GOOGLE_APPROVAL_RESPONSIBILITIES.md` (Jan vs Jake split), `GMAIL_GOOGLE_APPROVAL_GUIDELINES.md` (reference), `GMAIL_GOOGLE_APPROVAL_PLAN.md` (Jake-facing plan)

---

## 1. Bottom line

Nothing has been submitted to Google yet, so the verification review clock still has not started. Preparation is roughly 70% complete and, importantly, **is not blocked by anything on Jake's side**. The main change since the last revision is bad news: production Gmail inbound has been dead since 2026-07-08, and the watch-renewal mechanism I built did not save it. Restoring that is now the top priority, both operationally and because it blocks the demo video.

---

## 2. The key framing: two separate Google tracks

These two efforts have been blurring together in the email threads. They are independent.

**Track A, the OAuth verification.** This is the actual approval that lets any customer connect Gmail and Calendar without the "unverified app" warning, and that lifts the 100-user cap. All of it happens inside the existing `velvet-vles` Cloud project. Nothing about it depends on the Workspace domain saga.

**Track B, the Google Workspace domain claim.** This gets the company its own email on `velvetelves.com` and creates the organization that would let the Cloud project move off Jake's personal account. It is stuck in Google's queue.

**Track B does not block Track A.** The entire submission package can be finished while the domain situation sits unresolved. The only thing Track B genuinely gates is the optional project-ownership migration, which was always a "nice to do before submission," not a prerequisite.

---

## 3. Critical issue: production Gmail inbound is down

**Symptom.** The prod Gmail watch expired on 2026-07-14 and was never renewed. The last successful inbound sync was 2026-07-08. Roughly two weeks of inbound transaction mail has not been processed.

**Root cause.** The renewal I built has two paths, and this scenario defeated both:

- The opportunistic renew-after-sync path lives inside the webhook, so it only fires when a notification arrives. Once the mailbox went quiet, there was no trigger to renew it.
- The `renew-due` scan endpoint, which exists precisely to cover idle mailboxes, is deployed but was never attached to a scheduler. Nothing ever called it.

So the mailbox went idle, the 7-day watch aged out, and no mechanism woke it back up. This is the exact gap recorded as an open item in the earlier revision; it has now actually bitten.

**Compounding factor.** While the app remains in Testing mode, Google expires refresh tokens roughly weekly. The stored token is therefore probably dead as well, which means a plain renewal call would likely fail on authentication. A full reconnect (fresh consent) is the reliable fix.

**Consequences.** Beyond the operational outage, this blocks recording the demo video, since that requires a live connect-receive-send flow. It also means the "backend renews the watch daily" claim still sitting in the guidelines is demonstrably false and must be corrected before it goes into Google's security answers.

---

## 4. Verified healthy right now (checked 2026-07-23)

- Public pages are live: `https://velvetelves.com/privacy` returns 200 and contains the exact Limited Use statement, and `https://velvetelves.com/data-deletion` returns 200.
- Both Google domain-verification DNS records still resolve correctly (`73007731` and `zpe5vbcep7bb`).
- The scope trim is shipped and deployed, leaving a single restricted scope.
- Route 53 is fully healthy: registrar delegation matches the hosted zone exactly, so DNS ownership is provable.

---

## 5. Final scope set

The submission covers these, all on one OAuth client:

- `openid`, `email`, `profile` (basic, account identity)
- `gmail.send` (sensitive), used only for user-approved replies
- `gmail.readonly` (restricted), inbound reading for transaction matching and draft preparation
- `calendar.events` (sensitive), writing transaction deadlines to the user's calendar

`gmail.modify` was removed after I verified in the code that nothing ever called a mailbox-modifying endpoint. That leaves exactly one restricted scope, which is the narrowest defensible footprint and removes Google's most common rejection reason.

Calendar is a required product feature, so it is included by default and needs no owner sign-off.

---

## 6. Settled inputs

- Legal entity: Orange Door, LLP dba Velvet Elves, organized in Indiana. Already written into the privacy policy.
- Support address: `support@velvetelves.com`. Monitoring falls to the owners by default, since Jake and Audri handle company mail and will front the review correspondence.

---

## 7. Track B detail: the Workspace domain situation

Jake's Workspace signup is jammed in a loop. The sequence: an early partial signup left `velvetelves.com` attached to a half-finished Google account, which produced "this domain name is already in use." He filed a domain-release request (reference #73007731). Google confirmed by email that the DNS ownership check passed, but the final Submit button on the Admin Toolbox page never registered, in any browser. Because that request stayed open, the recovery tool now reports the domain is "being taken over by another administrator," and every fresh attempt bounces back to a generic help article.

Diagnosis: the "other administrator" is our own dead request. I verified via the AWS CLI that Route 53 is entirely healthy and that no DNS change can affect this, since the block is an account-state conflict on Google's side.

Current plan: let the stuck request expire (filed 2026-07-07, so that window has now passed), then rerun the tool start to finish in one sitting. The reference number the tool issues *is* the DNS record name, so a rerun needs a fresh record from me in real time. Jake must ping me before starting so I can add it within minutes and he can verify and submit without the multi-day gap that likely killed the first attempt.

Side effect discovered along the way: GoDaddy discontinued catch-all forwarding and silently dropped the existing forwards, which is why mail to the domain was bouncing. I ruled out SendGrid as a cause by auditing the zone: every SendGrid record is an outbound-only CNAME on its own subdomain, and the only MX in the zone still points at GoDaddy. Jake has since recreated named forwards for jake@, audri@, info@, support@, admin@, noreply@ and payments@, and on 2026-07-23 added `hello@` and `invitations@` to cover the two platform sender addresses that were still bouncing. Inbound mail on the domain is fully restored.

---

## 8. What I need from Jake

**Closed as of 2026-07-23.** Jake added the `hello@` and `invitations@` forwards and sent the confirming test to `support@`. The email infrastructure gap is fully closed: every address the platform sends from now has a working inbound path, so replies no longer bounce, and `support@velvetelves.com` is confirmed reaching me. Nothing about our outbound mail or the public support contact is blocked any more.

**Still open, neither urgent today.**

1. **The Workspace rerun**, whenever he is ready, following the ping-me-first protocol in section 7. He starts the tool, sends me the new reference number the moment it appears, I add the DNS record within minutes, and he verifies and submits in one sitting.
2. **Security-assessment budget pre-clearance.** Raised previously, never answered. Not blocking until Google actually requires an assessment. If it does, engaging and paying an approved assessor is the owners' task; I advise on approach and supply the technical evidence, and I do not engage or commit spend.

Nothing about the submission itself is requested yet. That ask comes only when the package is ready.

Worth noting: `support@` now working does **not** resolve the consent-screen support-email constraint in Task 4. That dropdown needs an address backed by a real Google account, and a working GoDaddy forward is still not one.

---

## 9. My task list

Each task below gives the concrete steps, the exact values, the "done when" test, and the gotcha that is most likely to waste an afternoon. All Console work happens in project **Velvet Elves / `velvet-vles`** (project number 538509143953). All DNS work happens in Route 53 hosted zone **`Z04016973TWW2D0EKIMFB`**.

### Immediate, because it unblocks the rest

#### Task 1. Restore prod Gmail inbound

**Steps.** Sign in to the production app as the user holding the Gmail connection. Go to Settings, then Integrations. Disconnect Gmail, then Connect it again and complete Google's consent screen. Disconnect first rather than just reconnecting: it guarantees a clean row and a brand-new refresh token instead of reviving a dead one.

**Done when.** In the prod database, the Gmail integration's `metadata_json.gmail_watch.expiration_iso` sits roughly seven days in the future and `created_at` or `renewed_at` shows today. Then send a real test email to the connected mailbox and confirm three things: `lastSyncedAt` updates, the message appears on the matching transaction, and a draft lands in AI Email Review.

**Gotchas.** The connected Google account must still be on the consent screen's test-user list, or the connect will fail with a 403 before it ever reaches our callback. Also, this restores service but does not fix the underlying cause, so do not close this out until Task 2 is done, otherwise the same outage returns in about a week.

#### Task 2. Wire a daily scheduler for watch renewal

**What to call.** `POST /api/v1/integrations/gmail/watches/renew-due`, currently protected by `require_role(UserRole.ADMIN)`.

**The auth problem to solve first.** A cron job cannot hold a user JWT, since they expire. Two options: add a machine-caller path to this endpoint that accepts a shared secret header, mirroring the existing `EMAIL_WEBHOOK_SECRET` pattern already used by the Pub/Sub webhook, or mint a long-lived token for a dedicated service admin user. The shared secret is cleaner, matches a pattern already in the codebase, and avoids a permanent privileged user account. Do this before wiring the scheduler.

**Scheduler options.** Prefer AWS EventBridge Scheduler pointed at an API destination, because the infrastructure already lives in AWS alongside the ECS service and the secret can live in Secrets Manager. The lighter alternative is a scheduled GitHub Actions workflow that curls the endpoint using a repository secret, which is faster to stand up but ties production health to GitHub.

**Do not** run this as an in-process background loop inside FastAPI. Production runs two ECS tasks, so it would double-fire, the same multi-instance trap that previously broke in-memory OAuth state.

**Cadence and margin.** Daily is right. Consider widening the scan's renewal threshold from 24 to 48 hours so a single failed run cannot cause an outage; a watch lives seven days, so there is ample margin.

**Done when.** A manual call returns a summary like `{"checked": N, "renewed": M, "failed": 0}`, the next day's scheduled run appears in CloudWatch logs, and an alert exists (or at minimum a log filter) for any run reporting `failed > 0`.

### Then the submission package, all doable now without Jake

#### Task 3 (M4). Set the consent-screen scopes

**Navigate.** Console, correct project selected, then APIs and Services, then OAuth consent screen, which opens the Google Auth Platform area. Choose **Data Access**, then **Add or remove scopes**.

**The list must be exactly these six.** `openid`; `.../auth/userinfo.email`; `.../auth/userinfo.profile`; `https://www.googleapis.com/auth/gmail.send`; `https://www.googleapis.com/auth/gmail.readonly`; `https://www.googleapis.com/auth/calendar.events`.

**Remove** `gmail.modify` if present. That single removal is the main point of this task. Also confirm nothing broader crept in: no `mail.google.com`, no `gmail.metadata`, no calendar scope beyond `calendar.events`. To add anything missing, paste the full scope URL into the "Manually add scopes" box, click Add to table, then tick it. Finish with Update, then Save.

**Done when.** Data Access lists precisely those six, with `gmail.readonly` grouped under Restricted and both `gmail.send` and `calendar.events` under Sensitive.

#### Task 4 (M5). Complete consent-screen branding

**Navigate.** Google Auth Platform, then **Branding**.

**Values.** App name `Velvet Elves`. Application home page `https://velvetelves.com/`. Privacy policy `https://velvetelves.com/privacy`. Terms of service `https://velvetelves.com/legal`. Authorized domain `velvetelves.com`. Developer contact email: an address actually monitored.

**Logo.** Must be square. Use roughly 120 by 120 pixels, PNG or JPG, comfortably under 1 MB. Source it from the existing brand logo asset; do not invent a new mark. Be aware that uploading a logo triggers Google's brand verification, which is part of what the review covers.

**The gotcha that will cost time.** The **User support email** field is a dropdown, not a free-text box. Google only offers the signed-in account's own address plus Google Groups that account owns. Because `support@velvetelves.com` is currently just a GoDaddy forward and not a Google account, **it will probably not be selectable until Workspace exists**. Do not stall on this. Select an address tied to a real Google account we control, keep `support@velvetelves.com` as the published support address on the public pages, and switch the dropdown over once Workspace lands. This is the one place where Track B touches Track A, and only cosmetically.

**Done when.** Every field saves without validation errors and the authorized domain is accepted, which requires Task 5.

#### Task 5 (M6). Verify the domain in Search Console

**Steps.** Go to Search Console and sign in with the **same Google account that owns or edits the `velvet-vles` project**, because Google requires the authorized domain to be verified by a project owner or editor. Add a property, choose the **Domain** type (it covers all subdomains), and enter `velvetelves.com`. Google issues a TXT value. Add it in Route 53, then click Verify.

**The Route 53 gotcha.** The apex already holds a TXT record with the value `D2638555`. Route 53 keeps every TXT value for one name inside a single record set, so this new value must be **merged into that existing record set**, never created as a second apex TXT. Creating a second one either fails or silently destroys the existing value. Read the current set, then UPSERT with both values present.

**Done when.** Search Console reports the property verified, and `velvetelves.com` is accepted as the authorized domain on the Branding page.

#### Task 6 (M7). Write the three scope justifications

Write roughly 100 to 150 words per scope. Each should name the concrete feature, the Google API methods it calls, the exact screen where a user sees the result, and why a narrower scope would not work. Never describe the AI as autonomous.

- **`gmail.readonly`.** Reads inbound transaction mail so it can be matched to the right deal, logged in that deal's communication history, and used as context for a draft reply. Calls `users.watch`, `users.history.list`, and `users.messages.get`. Visible in the deal's Email tab and the AI Email Review queue. A metadata-only scope is insufficient because matching and drafting both need message content.
- **`gmail.send`.** Sends a single transaction-specific reply only after the user clicks Approve and Send or Edit and Send, from the user's own address, and records it on the transaction. Calls `users.messages.send`. No autonomous or bulk sending exists anywhere in the product.
- **`calendar.events`.** Writes transaction deadlines to the user's calendar when the user connects Calendar and chooses to sync. Limited to event creation and update; no read of unrelated calendar data beyond what the feature needs.

**Done when.** Three paragraphs exist, each naming API methods and a specific screen, ready to paste into the Verification Center.

#### Task 7 (M8). Record the demo video

**Prerequisites.** Task 1 complete (a live Gmail connection is mandatory), a dedicated test Google account on the tester list, and a seeded test transaction. No real client data on screen at any point.

**Shot list, in this order.** Public home page and the privacy page, including the Limited Use text. Sign in to the app. Settings, then Integrations. Click Connect Gmail and show the **entire Google consent screen**, with the app name and every requested permission legible. Return to the connected state. Show an inbound email arriving and landing on the correct transaction. Show the AI-generated draft, stating clearly that it is a draft awaiting human approval. Click Approve and Send, then show the sent message in the test mailbox. Connect Calendar and show an event being written. Finally, Disconnect.

**Specs.** Unlisted on YouTube, six to ten minutes, browser address bar visible throughout, readable zoom level.

**Never** say the AI sends email automatically, and never demo a scope not being requested.

**Done when.** Uploaded as unlisted and the link is saved into the submission package.

#### Task 8 (M9). Assemble the security evidence packet

Produce one folder containing: an architecture diagram (browser, FastAPI backend, Supabase, Gmail API, Pub/Sub, Calendar API, AI provider, email provider); a data-flow diagram covering connect, inbound sync, AI draft, send, calendar write, disconnect, deletion; a scope-to-API-method mapping; the token storage design (encryption at rest, key location, rotation, access control); the PII encryption design from `SYSTEM_DESIGN.md`; the multi-tenant isolation design from `MULTI_TENANCY_IMPLEMENTATION_PLAN.md` with passing isolation tests; proof of the logging policy (no tokens, no auth codes, no raw Pub/Sub JWTs, no full message bodies, addresses masked); the vulnerability and dependency scanning process with evidence and criticals remediated; the incident response plan including notifying Google of any Google-data incident; the retention and deletion policy; and the subprocessor list with AI-provider terms proving no training on our data.

Most of this already exists in the codebase and design docs. The genuinely new work is drawing the two diagrams and writing the short policy statements.

**Done when.** Every item exists as a file in one folder, ready to hand to an assessor without further assembly. Remember that if Google requires a paid assessment, engaging and paying the assessor is the owners' task, not mine.

#### Task 9. Correct the false "renews daily" claim

**Exact locations.** `GMAIL_GOOGLE_APPROVAL_GUIDELINES.md` line 294 ("Backend renews `users.watch` daily, before the 7-day expiration window"), line 432 ("Renew Gmail watches daily"), and line 560 (the checklist item "Gmail watch renewal exists and is monitored"). Also `GMAIL_PUBSUB_WEBHOOK_CONFIGURATION_GUIDE.md` line 17.

**Replace with the real mechanism.** Renewal happens opportunistically inside the Gmail webhook after each successful history sync, which sustains active mailboxes, plus a `renew-due` scan endpoint driven by a daily scheduler that covers idle mailboxes.

**Sequencing note.** Once Task 2 ships, this description becomes true and can be stated confidently. Until then it is a false claim heading straight into Google's security answers, which is exactly the kind of statement an assessor tests.

**Done when.** No document asserts a renewal behavior the code does not actually perform.

#### Task 10 (M10). Assemble the submission package for Jake

One document containing: the precise Console screens to click in order (publish to Production, open Verification Center); the paste-ready scope justifications from Task 6; the documentation links (home, privacy, data deletion); and the unlisted video URL. Jake performs the submission and fronts reviewer correspondence; my job is to leave him zero technical decisions.

**Done when.** A non-technical person can complete the entire submission by following it without asking a single question.

### Deferred

Moving the `velvet-vles` project into a Workspace organization. This waits on Track B and is optional relative to submission, though cleaner to do before submitting since verification attaches to the project.

---

## 10. Risks and standing issues

- **Testing-mode token expiry.** Until the app is published to Production and verified, tokens expire roughly weekly and testers' Gmail connections keep dropping. This is a symptom of being unverified, not a bug, and it will recur until approval.
- **Idle-mailbox renewal.** Fixed only once task 2 lands. Until then, the same outage can repeat.
- **Webhook hardening.** Duplicate-integration handling and an "unhealthy, reconnect" UI state remain queued. Worth landing before Google's reviewers exercise the live flow.
- **Calendar coupling.** `calendar.events` shares the OAuth client, so it is reviewed alongside Gmail and must appear in the scope list, justifications, and demo video.
- **Project ownership.** The Cloud project still lives under Jake's personal Google account, which is a single point of failure until the Workspace migration happens.

---

## 11. Timing and the strategic argument

Once submitted, Google's review typically takes three to six weeks, or up to about eight if a security assessment is required. That window is not compressible and runs in parallel with all other launch work.

The argument for pushing now: the weekly token expiry that keeps killing Gmail connections is a direct consequence of being unverified. Every week the submission slips is another week of testers being silently disconnected and another week of outages like the current one. Since Track A is unblocked, the correct move is to drive tasks 1 through 10 to completion rather than waiting on the domain.
