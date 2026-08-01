# Google Approval Package — Playbook

**Date:** 2026-08-01
**Prepared by:** Jan
**Purpose:** exactly how the Google verification submission package gets built, what "done" means, how it is handed to Jake, and what Jake does with it. This is the operational guide for the final stretch; the status history lives in `GMAIL_GOOGLE_APPROVAL_STATUS_REPORT.md`.

---

## 1. The rule that governs everything in this document

**I prepare; Jake executes.** I produce every material and every guideline, ending in one package document with zero technical decisions left open. Jake personally performs the submission using that package, fronts Google's review correspondence, and makes any spending decision (the possible paid security assessment). I never submit, never engage a vendor, never spend. This split is fixed and is restated at each handoff point below.

---

## 2. What the finished package contains

The package is **one document** (plus one video link) that I hand to Jake. Its contents, in the order he will use them:

1. **A pre-flight checklist** confirming everything is already configured (scopes, branding, domain, public pages) so he changes nothing, only submits.
2. **Step-by-step Console instructions with screenshots**: sign in, select project `velvet-vles`, publish the app to Production, open the Verification Center, begin verification.
3. **Paste-ready answer blocks**: the three scope justifications (Section 6 below), the app description, and the documentation links.
4. **The links list**: home, privacy, data deletion pages, and the unlisted demo video URL.
5. **The "during review" protocol** (Section 8): forward every Google email to me the same day; I draft the reply; he sends it; nobody changes anything in the Cloud project until approval.

**Done-criterion for the package:** a non-technical person can complete the entire submission by following it without asking a single question. If any step requires judgment, the package is not finished.

---

## 3. Preparation steps (mine), in execution order

### P1 — Fix the inbound-dispatch bug (code; gates the video)

The subject-tag matcher runs `.ilike("id", tag)` against the uuid `id` column (`inbound_dispatch.py` ~line 544), which throws Postgres 42883 and kills dispatch for every tagged email.

- Fix: fetch the tenant's transaction ids and prefix-match in Python, or cast the column to text in the query.
- Add a regression test: a tagged inbound email must match its transaction and produce a draft.
- Validate on stage end to end: send the tagged test email, confirm it lands on the deal and a draft appears in Email.
- Deploy to prod (the video is recorded against prod — see P6).

### P2 — Consent-screen scopes (M4; Console, project `velvet-vles`)

APIs & Services → OAuth consent screen → **Data Access** → Add or remove scopes. The list must be exactly:

- `openid`, `.../auth/userinfo.email`, `.../auth/userinfo.profile`
- `https://www.googleapis.com/auth/gmail.send` (sensitive)
- `https://www.googleapis.com/auth/gmail.readonly` (restricted)
- `https://www.googleapis.com/auth/calendar.events` (sensitive)

Remove `gmail.modify` if present. Nothing broader may appear (`mail.google.com`, `gmail.metadata`, other calendar scopes). Done when the grouping shows exactly one restricted scope.

### P3 — Consent-screen branding (M5; Console → Branding)

- App name: `Velvet Elves`
- Logo: square, ~120×120 px, PNG, from the existing brand asset (never a new mark)
- **User support email: `support@velvetelves.com`** — now selectable, since Workspace made it a real Google-backed address. The old workaround is retired.
- Home page `https://velvetelves.com/` · Privacy `https://velvetelves.com/privacy` · Terms `https://velvetelves.com/legal`
- Authorized domain: `velvetelves.com` (requires P4)
- Developer contact: a monitored address

### P4 — Search Console domain verification (M6)

- Sign in to Search Console **with the same account that owns/edits `velvet-vles`**.
- Add property → type **Domain** → `velvetelves.com` → Google issues a TXT value.
- **Route 53 warning:** the apex TXT record set already holds `"D2638555"` and `"v=spf1 include:_spf.google.com ~all"`. The new value must be **merged into that set** (UPSERT with all three values). A second apex TXT record set is impossible; overwriting loses the SPF and breaks mail authentication.
- Click Verify; done when the property is verified and Branding accepts the authorized domain.

### P5 — Scope justifications (M7; final texts in Section 6)

Already drafted; give them one read for accuracy against the current product, then freeze them into the package verbatim.

### P6 — Demo video (M8)

**Record against production**, because the video must show the OAuth client being submitted; stage uses a different Google project and client, and a mismatch is a known rejection cause. That makes these prerequisites:

- P1 deployed to prod.
- Prod Gmail reconnected (fresh token + watch; the old ones are dead).
- A dedicated test Google account on the tester list, a seeded test deal, no real client data anywhere on screen.

Shot list, in order: public home page and privacy page (Limited Use text visible) → sign in → Settings → Email & E-signature → Connect Gmail → **the full Google consent screen, app name and every permission legible** → connected state → a test email arriving and landing on the right deal → the AI draft (say clearly it is a draft awaiting human approval) → Approve & send → the sent message in the test mailbox → connect Calendar and show a deadline written to it → Disconnect.

Specs: unlisted YouTube, 6–10 minutes, address bar visible throughout, readable zoom. Never say the AI sends automatically; never show a scope not being requested. Done when uploaded and the link is in the package.

### P7 — Security evidence packet (M9)

One folder: architecture diagram; data-flow diagram (connect, inbound sync, AI draft, send, calendar write, disconnect, deletion); scope-to-API-method mapping; token storage design (encrypted at rest, key location, access control); PII encryption design (`SYSTEM_DESIGN.md`); tenant isolation (`MULTI_TENANCY_IMPLEMENTATION_PLAN.md`) with passing tests; logging policy (no tokens, no bodies, masked addresses); dependency/vulnerability scanning evidence; incident response plan (including notifying Google of any Google-data incident); retention and deletion policy; subprocessor list with AI-provider no-training terms.

This is not submitted with the verification; it is ready in case Google requires the CASA assessment, so the response is immediate instead of a scramble.

### P8 — Correct the "renews daily" claim

`GMAIL_GOOGLE_APPROVAL_GUIDELINES.md` lines ~294, ~432, ~560 and `GMAIL_PUBSUB_WEBHOOK_CONFIGURATION_GUIDE.md` line ~17 still say the backend renews the Gmail watch daily. Replace with the real mechanism: renewal after each successful webhook sync, plus the `renew-due` scan endpoint driven by the scheduler tick. No document may claim behavior the code does not perform — these texts feed the security answers, and a false claim there is exactly what an assessor tests.

### P9 — Assemble the package (M10)

Write the package document per Section 2, walking the Console myself in a test pass to screenshot each screen Jake will see. Final check against the done-criterion, then hand off.

---

## 4. The handoff

When P1–P9 are complete, I send Jake the package with a short cover note:

> The Google submission package is ready. Everything is pre-configured; nothing in the Console needs changing. Following the document top to bottom takes about half an hour. When you're ready to do it, ping me before you start and I'll be reachable throughout.

From that moment the task is his. My remaining role is being reachable during his half hour, then drafting review replies.

---

## 5. Jake's execution (his tasks, verbatim into the package)

1. Sign in at console.cloud.google.com, project **Velvet Elves (`velvet-vles`)**.
2. OAuth consent screen → publish the app to **Production**.
3. Open the **Verification Center** → prepare/start verification.
4. Paste the prepared answer blocks; attach the documentation links and the video URL.
5. Submit. Note the case/reference number and send it to me.

---

## 6. Paste-ready scope justifications (frozen text)

**gmail.readonly (restricted).** Velvet Elves reads inbound Gmail messages only for mailboxes a user explicitly connects. Incoming transaction-related messages are matched to the user's real-estate transaction, logged in that transaction's communication history, and used as context to prepare a draft reply for human review. The app calls `users.watch`, `users.history.list`, and `users.messages.get`. The feature is visible to the user in each deal's Email tab and the Email screen's Inbox. A metadata-only scope is insufficient because both transaction matching and draft preparation require message content.

**gmail.send (sensitive).** Velvet Elves sends a Gmail message only when the authenticated user clicks Approve & Send or sends an edited draft. Each send is a single transaction-specific reply, sent from the user's own connected address via `users.messages.send`, and recorded in the transaction's communication history. There is no autonomous sending and no bulk email anywhere in the product.

**calendar.events (sensitive).** When a user separately connects Google Calendar, Velvet Elves writes that user's transaction deadlines (closing dates and contract milestones) to their calendar at their request. Access is limited to creating and updating these events; the app does not read or process unrelated calendar data.

---

## 7. What Jake should expect after submitting

- Google's review typically takes three to six weeks; up to about eight if a security assessment is required. It cannot be accelerated.
- The unverified-app warning and the weekly token expiry both disappear only at approval — until then testers keep reconnecting weekly, which is expected.

## 8. During-review protocol (both of us)

- Google emails the submitter — Jake. He forwards each message to me the same day it arrives.
- I draft the reply within one business day; Jake sends it. Fast turnaround here is worth weeks of elapsed time.
- Nobody changes anything in the Cloud project (scopes, clients, branding) while the review runs; changes can reset it.
- **If Google requires the CASA security assessment:** choosing, engaging, and paying an approved assessor is Jake and Audri's decision and action. I supply the P7 evidence folder and advice on selecting an assessor. I do not engage or commit spend.

---

## 9. Current blockers snapshot (2026-08-01)

- P1 (inbound bug) — not started; gates P6.
- Prod Gmail reconnect + prod deploy — needed for P6; prod scheduler wiring rides the same deploy.
- P2–P5, P7, P8 — unblocked, can run in parallel today.
- Jake — nothing to do until the handoff in Section 4.
