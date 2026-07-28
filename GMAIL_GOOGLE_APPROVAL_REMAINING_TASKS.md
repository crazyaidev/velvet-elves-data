# Gmail + Calendar Google Approval: Remaining Tasks (Jan vs Jake)

**As of:** 2026-07-23
**Prepared by:** Jan
**Companion docs:** `GMAIL_GOOGLE_APPROVAL_STATUS_REPORT.md` (full status + per-task detail), `GMAIL_GOOGLE_APPROVAL_MATERIALS_AND_STEPS.md`, `GMAIL_GOOGLE_APPROVAL_RESPONSIBILITIES.md`

---

## Framing

Nothing has been submitted to Google yet, so the review clock has not started. One point up front: the Workspace domain saga is **not** on the approval critical path. The submission happens in the existing `velvet-vles` project, so approval depends only on me finishing the package and Jake submitting it. Workspace is a parallel effort for company email and project ownership.

---

## Tasks I handle (technical work and all materials)

### A. Get the inbound to draft flow actually working

This is what the demo video has to show, and it is currently broken.

- Fix the inbound-dispatch bug found 2026-07-23 (the `ILIKE` on the uuid `id` column in `inbound_dispatch.py` that fails every tagged email with Postgres error 42883). This blocks tagged replies in production, not just our test.
- Re-validate stage inbound end to end after the fix: resend the tagged email, confirm it matches the deal and produces a draft.

### B. Google Cloud Console configuration (in `velvet-vles`)

- **M4:** set the consent-screen scopes to exactly the final six (remove `gmail.modify`).
- **M5:** complete consent-screen branding: app name, square logo, home/privacy/terms URLs, authorized domain, and the support-email dropdown workaround (a real Google account for now, since the GoDaddy forward cannot be selected there).
- **M6:** verify `velvetelves.com` in Search Console, adding the TXT merged into the existing apex record in Route 53.

### C. Submission artifacts

- **M7:** finalize the three scope justifications (already drafted, needs a review pass).
- **M8:** record the unlisted demo video. Depends on A being fixed and a working Gmail connection on the submitted (prod) client.
- **M9:** assemble the security evidence packet (two diagrams plus short policy statements; most content already exists).
- Correct the false "renews daily" wording in the guidelines so it matches the real mechanism before it goes into Google's security answers.
- **M10:** assemble the submission package that leaves Jake zero technical decisions.

### D. Production reliability (currently deferred, but needed before the live demo and launch)

- Deploy the scheduler code to prod, fire one manual tick, then create the hourly EventBridge schedule.
- Reconnect prod Gmail to restore inbound (the scheduler prevents recurrence but cannot revive the dead token).

---

## Tasks Jake must handle personally

### Required for approval (on the critical path)

- **Perform the verification submission** in the Console using my package: publish to Production, walk the Verification Center, paste the prepared answers, attach the links and video, submit.
- **Front the reviewer correspondence** during review: forward each Google email the same day, and send back the answers I draft. Fast turnaround here is worth weeks.

### Conditional

- **Security-assessment budget:** if Google requires the independent (CASA) assessment, deciding on and paying an approved assessor is his, as the owner. I advise on approach and supply the technical evidence; I do not engage or spend.

### Parallel, not an approval blocker

- **Finish the Google Workspace domain claim** (the stuck takeover request), using the ping-me-first protocol so I can add the new reference-number DNS record in real time. This gets company email and lets the project move off his personal account, but the submission does not wait on it.

---

## Bottom line

The only things that truly gate Google's decision are: I finish the package (sections A through C, with D needed for the live demo), then Jake submits it and answers the reviewer. Everything on Jake's side beyond submitting and replying is either conditional or running in parallel.

The immediate next step on my side is the inbound bug fix, which unblocks both the demo and real tagged replies.
