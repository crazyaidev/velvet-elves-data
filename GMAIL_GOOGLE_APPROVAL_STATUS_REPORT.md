# Gmail Google Approval: Status Report

**As of:** 2026-07-09
**Prepared by:** Jan
**Companion docs:** `GMAIL_GOOGLE_APPROVAL_TODO.md` (working checklist), `GMAIL_GOOGLE_APPROVAL_RESPONSIBILITIES.md` (Jan vs Jake split), `GMAIL_GOOGLE_APPROVAL_GUIDELINES.md` (reference), `GMAIL_GOOGLE_APPROVAL_PLAN.md` (Jake-facing plan)

---

## Bottom line

We are in **pre-submission preparation, and nearly through it.** Nothing has been submitted to Google yet, so the verification review clock has not started. The important shift since last week: the two things that used to be genuine blockers (a business decision from Jake, and the public privacy pages) are now resolved, and the technical foundation is done, tested, and live in production. What remains before submission is Google Cloud Console configuration plus the submission artifacts (demo video, justifications, security packet). The one dependency still outside my control is Jake's Workspace/domain claim, which is in a waiting period but does not block the rest of my prep.

---

## Final scope decision (the foundation everything else is built on)

| Scope | Type | Status |
|---|---|---|
| `openid`, `email`, `profile` | basic | keep |
| `gmail.send` | sensitive | keep (approved-reply send only) |
| `gmail.readonly` | **restricted** | keep (inbound read for matching + drafts) |
| `gmail.modify` | restricted | **removed** |
| `calendar.events` | sensitive | same OAuth client, decision pending (see risks) |

Removing `gmail.modify` leaves a single restricted scope, which is the narrowest defensible footprint and takes Google's most common rejection reason off the table before a reviewer ever looks.

---

## Done and verified

- **Scope trim (J1)** — `gmail.modify` gone from the code, 52 tests green, and confirmed **live in prod** (backend on task def 17, deployed 2026-07-09).
- **Public pages (J7)** — `velvetelves.com/privacy` and `/data-deletion` are **live (HTTP 200)**, carrying the exact Limited Use statement, the per-scope Google-data disclosure, the AI/no-training disclosure, named subprocessors, and the entity name Orange Door, LLP dba Velvet Elves.
- **Watch auto-renewal (built + deployed + proven working)** — confirmed the prod mailbox's watch **renewed itself** on 2026-07-07 (new expiry 2026-07-14) and synced mail on 2026-07-08. The old "goes deaf every 7 days" failure is fixed in production, and the July 8 expiry deadline is behind us with no manual action needed.
- **Inbound pipeline** — proven end to end on both staging and prod (watch → Pub/Sub → webhook → sync → persist), including fixing a duplicate-integration storm on staging.
- **Company inputs (K1, K2)** — legal entity (Orange Door, LLP dba Velvet Elves, Indiana) and support address (`support@velvetelves.com`, live via GoDaddy catchall) received and already in the privacy policy.

---

## In flight (not blocking my prep)

- **Google Workspace + domain claim (K3)** — Jake decided yes and is mid-signup. He hit a domain-lock issue and requested Google free it up, which is in a stated **up-to-3-business-day** window. I have already placed both DNS verification records he was sent (the recovery CNAME `73007731` and the verification CNAME `zpe5vbcep7bb`), both live and resolving, so the moment the domain frees up he clicks Confirm and it passes.

---

## Remaining before I can hand Jake the submission (my work)

All Google Cloud Console work is in the `velvet-vles` project and cannot be scripted; the rest are artifacts.

1. **Consent-screen scopes match code (J4)** — set the Console scope list to exactly the trimmed set. Console UI.
2. **OAuth client hygiene (J3)** — verify the Calendar callback URI, remove any dev/local redirect URIs from the prod client. Console UI.
3. **Consent-screen branding (J5)** — app name, logo, support email, home + privacy URLs, authorized domain. Every input now exists (privacy page is live, support email confirmed).
4. **Search Console domain verification (J6)** — the OAuth authorized-domain check is a separate token from the Workspace ones; I add it the same way when I configure the consent screen.
5. **Publish app to Production** — it is currently in Testing (tester allowlist). This also ends the 7-day token expiry that keeps disconnecting testers.
6. **Demo video (J9)** — record the OAuth grant + each scope in use (inbound read, human-approved send, disconnect), test data only.
7. **Scope justifications (J10)** — one concrete per-scope paragraph.
8. **Security evidence packet (J11)** — architecture, token encryption, tenant isolation, logging policy, AI-provider no-training terms. Assume CASA may be required for `gmail.readonly`.
9. **Submission package (J12)** — assemble 1 to 8 into the step-by-step guide Jake follows.

---

## Submission and review (Jake + Google)

- **Jake submits (K5)** using my package: publish, walk the Verification Center, paste the prepared answers, attach links + video.
- **Review correspondence (K6)** — Google emails Jake; he forwards same-day, I draft the answers, he sends them.
- **Google review** — typically **3 to 6 weeks**, up to ~8 if they require the security assessment. Not compressible; it runs in parallel with all other launch work.

---

## Critical path and timing

The gating sequence now is: **Workspace/domain clears (Jake, in the 3-day window) → I finish consent-screen config + artifacts (roughly a week of my work, most of which I can do in parallel now) → Jake submits → review clock starts.** Realistically that still points to **submission in the second half of July**, with approval landing mid-to-late August, later only if the audit round triggers.

---

## Risks and standing issues

| Item | Note |
|---|---|
| **Testing-mode token expiry** | Until we publish to Production and get verified, unverified-app tokens expire ~weekly, so testers' Gmail connections keep dropping. It is expected, not a bug, and it is one more reason not to let submission slip. |
| **Calendar coupling (J8)** | `calendar.events` rides the same OAuth client, so it is reviewed alongside Gmail. Decide whether to include and demo it now, or accept Calendar showing the unverified screen until covered. |
| **Idle-mailbox renewal cron** | Active mailboxes self-renew via the webhook hook (proven). Idle mailboxes still need a daily call to the `renew-due` endpoint, which is deployed but not yet on a scheduler. Ties into the platform's known missing-scheduler gap. |
| **Webhook hardening** | The duplicate-integration handling and an "unhealthy, reconnect" UI state are queued; worth landing before Google tests the live flow, though not strict submission blockers. |
| **Guidelines wording** | The approval guidelines still say "renews daily"; I will correct that to the real mechanism (renew-after-sync + due-scan) before it goes into the security answers. |
| **Project ownership** | If we migrate `velvet-vles` into the new Workspace org, cleanest to do it before submission, since verification attaches to the project. |

---

## What I still need from Jake

Only the Workspace/domain claim (K3), which is already in motion. K1 and K2 are done. His next concrete action is clicking Confirm once the domain frees up; after that, his only remaining role is the submission itself (K5) and forwarding reviewer emails (K6), both of which come with my prepared package.

---

**In one line:** foundation done and live, blockers cleared, roughly a week of Console-plus-artifacts work stands between us and a Jake-submits-ready package, and the only external wait is the domain-unlock window that is already ticking.
