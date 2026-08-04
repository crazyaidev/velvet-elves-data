# Google Approval — The Critical Path (what actually blocks approval)

**Date:** 2026-08-03 (revised same day after inspecting the live Console)
**Prepared by:** Jan
**Purpose:** the short list. Only the work that genuinely gates Google's decision, in dependency order. Everything else is listed at the bottom as explicitly non-blocking, so it stops competing for attention.
**Related:** `GMAIL_GOOGLE_APPROVAL_PACKAGE_PLAYBOOK.md` (full detail per step), `GMAIL_GOOGLE_APPROVAL_STATUS_REPORT.md` (history and state)

---

## What changed in this revision

The first version of this document was written from assumption. Inspecting the actual Google Auth Platform screens corrected three things, two of them materially:

1. **Domain verification was already done.** `velvetelves.com` is accepted and saved as an authorized domain, so the Search Console trip and the risky apex TXT merge are both off the table. Jake's Workspace verification last week covered it.
2. **The scope list is not wrong, it is empty.** All three Data Access sections read "No rows to display." The task is not "remove `gmail.modify`" (nothing was ever declared); it is "declare all six scopes from scratch."
3. **Two branding fields are wrong or missing**, and one of them is blocked on Jake for a root cause worth naming: no `@velvetelves.com` identity has access to the Cloud project at all.

Net effect: one blocker eliminated, one blocker turned out to be larger than described, one new dependency on Jake surfaced.

---

## Status at a glance

- **Blocker 1 — domain verification: DONE.**
- **Blocker 2 — declare the scopes: DONE 2026-08-03.**
- **Blocker 3b — app logo: DONE 2026-08-03** (uploaded `velvet-elves-frontend/public/logo.png` as-is).
- **Blocker 3a — user support email: the only branding field left. Blocked on Jake.**
- **Blocker 4 — publish to Production: DONE 2026-08-03.** Status now reads "In production", User type still External, cap 5/100, and a "Back to testing" control remains if it is ever needed. The expected "your app requires verification" banner appeared and was deliberately not acted on — that submission is Jake's.
- **Blocker 5 — demo video: the only substantial work left.**

Also done, not a blocker but worth recording: **developer contact** is now `info@velvetelves.com` plus `crazyaidev20500519@gmail.com` — two people, one of them a company-owned address, so Google's project notifications during review do not depend on a single person forwarding them.

---

## Blocker 1 — Domain verification — DONE

`velvetelves.com` sits in **Authorized domain 2** on the Branding page, saved, with the Save button greyed out (no pending edits). Google does not accept an unverified domain in that field, so ownership is already proven for this project.

`kbgvnsjdkgzixpeazmtn.supabase.co` occupies Authorized domain 1. That is the Supabase host behind "Sign in with Google" and **must stay** — removing it breaks that login path.

No Search Console work is needed. No DNS change is needed. In particular, **do not** touch the apex TXT record set: it now holds `"D2638555"` plus `"v=spf1 include:_spf.google.com ~all"`, and the SPF value is what makes Workspace mail authenticate.

---

## Blocker 2 — Declare the six scopes — DONE 2026-08-03

**Verified saved in the Console** ("Data access changes saved!"), with the three sections sorting exactly as intended:

- **Non-sensitive:** `userinfo.email`, `userinfo.profile`, `openid`
- **Sensitive:** `calendar.events` ("View and edit events on all your calendars"), `gmail.send` ("Send email on your behalf")
- **Restricted:** `gmail.readonly` ("View your email messages and settings") — and nothing else

**Exactly one restricted scope**, which was the target. Nothing broader present. The record of how this was done, and why it mattered, is kept below.

---

Console → Google Auth Platform → **Data Access**.

**State before the fix: completely empty.** "Your non-sensitive scopes", "Your sensitive scopes" and "Your restricted scopes" all read "No rows to display."

**Why the app still works anyway.** The scopes the code requests live in the runtime authorization URL, not in this list. While the app is in **Testing** status, Google honors those runtime-requested scopes for test users regardless of what is declared here. That is why Gmail connections keep succeeding, and why the live production connection checked on 2026-08-01 showed exactly `gmail.send` and `gmail.readonly` granted with no `gmail.modify`. The code is correct; only the Console declaration is absent.

**Why it must be fixed.** This declared list is what Google actually reviews during verification. Submitting with it empty means there is nothing to approve.

### How to fill it

Click **Add or remove scopes**. The three basic scopes are already visible at the top of the panel, so tick them directly:

- `https://www.googleapis.com/auth/userinfo.email`
- `https://www.googleapis.com/auth/userinfo.profile`
- `openid`

For the other three, use the **Filter** box (type `gmail`, then `calendar`) — both APIs are enabled on the project, so they will be present in the list. If filtering is awkward, use **Manually add scopes** at the bottom of the panel and paste these one per line, then click **Add to table**:

```
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/calendar.events
```

Then **Update**, then **Save**.

### The check that proves it is right

After saving, the sections should sort themselves:

- **Non-sensitive:** `userinfo.email`, `userinfo.profile`, `openid`
- **Sensitive:** `gmail.send`, `calendar.events`
- **Restricted:** `gmail.readonly` — and nothing else

**Exactly one restricted scope** is the outcome that matters. That single row is the payoff for the `gmail.modify` removal done in the code on 2026-07-06, and it is the narrowest defensible footprint for the product.

Nothing broader may appear: no `mail.google.com`, no `gmail.metadata`, no calendar scope beyond `calendar.events`.

---

## Blocker 3 — Branding

### Confirmed correct and saved

- App name: `Velvet Elves`
- Application home page: `https://velvetelves.com/`
- Application privacy policy link: `https://velvetelves.com/privacy`
- Application terms of service link: `https://velvetelves.com/legal`
- Authorized domains: `kbgvnsjdkgzixpeazmtn.supabase.co`, `velvetelves.com`
- Developer contact: `info@velvetelves.com` (a real Workspace alias reaching Jake)

### 3a — User support email is a personal Gmail (blocked on Jake)

Currently `crazyaidev20500519@gmail.com`. This is displayed to users on the consent screen and is cross-checked by reviewers against the public pages. The live privacy policy tells users to contact `support@velvetelves.com`, so the two disagree, and a personal `@gmail.com` on a commercial restricted-scope submission undermines credibility.

**Root cause, confirmed by opening the dropdown:** it offers only `crazyaidev20500519@gmail.com` and reports "Google Groups managed by you — No groups". That dropdown only ever lists the signed-in account's own address plus Groups it manages. **No `@velvetelves.com` identity has access to the `velvet-vles` project at all** — Jake's Owner grant is on `jakestiles@gmail.com`, his personal account, not on `jake@velvetelves.com`. So no company address can appear.

A second trap: a Google Group cannot be created at an address that already exists as a user alias. `support@velvetelves.com` is currently an alias on Jake's user, so it must be removed first, and Google can take time to free the address for reuse.

**The ask to Jake (sent 2026-08-03):**

1. Create `jan@velvetelves.com` and grant it **Owner** on the `velvet-vles` project (IAM → Grant access). This alone unblocks the field and gives a company identity for all future Console work.
2. When convenient, convert `support@velvetelves.com` from an alias into a **Google Group** with both of them as managers. This is the ideal end state and also delivers the "reaches multiple people" outcome Jake raised himself after the mail cutover.

Item 1 is the blocking one. With it, the support email can be set to `jan@velvetelves.com` and the personal-Gmail problem disappears; item 2 upgrades it to a true shared support address afterward.

### 3b — App logo — DONE 2026-08-03

Uploaded `velvet-elves-frontend/public/logo.png` unchanged (1024x1024, 487 KB, PNG), which satisfies every requirement Google states: square, allowed format, under 1 MB.

**Why the original rather than a cropped icon.** A cropped character-only square was produced and is kept at `velvet-elves-data/velvet-elves-oauth-logo.png` (512x512) in case it is ever wanted for a favicon or tighter icon context. It was not used, for a good reason: uploading a logo triggers **brand verification**, in which a reviewer compares the consent screen against the website and app. `logo.png` is the asset used throughout the frontend and marketing site, so an exact match is the most straightforward thing for a reviewer to confirm. A variant existing nowhere else in the product is a weaker position. The Console thumbnail also confirmed the wordmark stays legible at small size, which was the original concern.

Note from Google's own text on that page: uploading a logo triggers brand verification as part of the review. Acceptable here since a restricted scope means full verification regardless.

---

## Blocker 4 — Publish the app to Production — DONE 2026-08-03

Console → Google Auth Platform → **Audience** page.

**Verify-after note.** Publishing removes the 7-day refresh-token expiry only for tokens issued **after** the change; tokens already issued under Testing keep their original expiry. So an existing connection must be disconnected and reconnected to benefit. Also worth knowing: refresh-token lifetime is not observable anywhere in our data (`metadata_json.token_expires_at` is the one-hour *access* token). The proof that publishing worked is negative evidence — the connection surviving past seven days rather than dying.

The record of why this was done, and why it did not need to wait, is kept below.

---

**Ordering: this had to come after Blocker 2** (publishing with an empty scope list while the app requests restricted scopes at runtime invites errors). Blocker 2 closed on 2026-08-03, so this is now unblocked.

**It does NOT need to wait for Blocker 3a (the support email).** An earlier revision of this document said to wait until branding was fully clean; that was over-cautious. The support email field is populated and valid, so publishing passes validation, and **consent screen fields stay editable after publishing** — the lock-in risk only begins once the app is *submitted for verification*, which has not happened. So publish now and swap the support email whenever Jake provisions the account.

**A second benefit beyond the token expiry.** Dead refresh tokens cannot renew a Gmail watch — that is exactly why all five watch renewals failed with `invalid_grant` during the staging tick on 2026-07-23. Publishing stops tokens expiring weekly, which lets renew-after-sync actually function instead of failing on auth. Publishing therefore improves inbound reliability, not just tester convenience.

**Recommended order:** publish → reconnect prod Gmail (the new token will not expire in 7 days) → record the demo video against that stable connection. This also disposes of the 2026-08-05 watch expiry as a side effect.

**When publishing, decline any prompt to submit for verification.** The demo video is not recorded yet, and the submission itself is Jake's to perform through the Verification Center using the prepared package.

**Why do this before submitting rather than leaving it to Jake:** the weekly Gmail disconnects interrupting Audri and Jake's testing are caused by **Testing publishing status**, not by being unverified. Google expires refresh tokens 7 days after issue for apps in Testing. Publishing to Production removes that limit immediately, even before verification is granted. The unverified-app warning screen remains until approval, but the weekly reconnect pain stops. That is real relief for the testing round currently running.

---

## Blocker 5 — Record the demo video

**Prerequisites are met.** Production Gmail was verified healthy on 2026-08-01: one active integration, watch alive, and the trimmed scope set confirmed on a live production consent. Also needed: a dedicated test Google account and a seeded test deal, with no real client data visible at any point.

**Record against production**, because the video must show the OAuth client actually being submitted. Staging runs on a different Google project and client, and a mismatch between the video and the submitted client is a known rejection cause.

Shot list, in order:

1. Public home page and the privacy page, with the Limited Use text visible
2. Sign in to the app
3. Settings → Email & E-signature
4. Click Connect Gmail and show the **entire Google consent screen**, app name and every requested permission legible
5. Return to the connected state
6. A test email arriving and landing on the correct deal
7. The AI draft, stating clearly that it is a draft awaiting human approval
8. Approve & Send, then the sent message in the test mailbox
9. Connect Calendar and show a transaction deadline being written
10. Disconnect

Specs: unlisted on YouTube, six to ten minutes, browser address bar visible throughout, readable zoom. Never say the AI sends automatically. Never show a scope that is not being requested.

---

## Then hand to Jake

The three scope justifications are already written and frozen in `GMAIL_GOOGLE_APPROVAL_PACKAGE_PLAYBOOK.md` Section 6, so that is a proofread, not a task.

Once the blockers are closed, Jake receives one document and performs the submission through the **Verification Center** (visible in the same left nav): paste the prepared answers, attach the documentation links and the video URL, submit, and send back the case number. During review he forwards every Google email the same day; Jan drafts the replies; Jake sends them.

---

## Explicitly NOT blocking — stop carrying these

**Security evidence packet.** Only matters if Google demands the CASA assessment, which may never happen. Prepare it while waiting for the review, not before submitting.

**Scheduler and Gmail watch renewal.** Operational reliability, not approval criteria. One dated risk worth managing: if the production watch expires mid-review while a Google reviewer is testing the app, inbound looks broken. The current watch runs to **2026-08-05**, so either reconnect manually or create the schedule before then.

**The inbound-dispatch bug fix.** Already implemented and tested in the working tree (266 tests green); it only needs committing. It does not gate approval.

**Project ownership migration into the velvetelves.com organization.** Does not gate approval. Recommendation: submit first, migrate after approval, since verification attaches to the project and survives a move. Note that Blocker 3a's fix (creating `jan@velvetelves.com` with project access) is the first practical step toward that migration anyway.

---

## Sequencing from here (as of 2026-08-03, after Blocker 2 closed)

1. **Now, unblocked:** Blocker 3b (upload the logo) — Jan, Console-only, a few minutes.
2. **Also now, in parallel:** Blocker 5 (record the demo video). Independent of everything else and the largest remaining piece of work.
3. **When Jake responds:** Blocker 3a (set the support email to a company address).
4. **After 3 is clean:** Blocker 4 (publish to Production). No longer gated by scopes.
5. **Then:** assemble the package and hand to Jake for submission.

**Only two things now stand between here and the handoff: the logo and the video.** Everything else is either done or waiting on one small Jake action.

---

## Incidental observation (not part of the submission)

The Console project picker shows `velvet-vles` under **"No organization"**, independently confirming the project is orphaned with no org parent — the condition that `jan@velvetelves.com` plus the eventual migration would resolve.

The same picker also lists another project named **"Velvet"** (`golden-manifest-489918-f0`), alongside "My First Project". Probably strays from early experimentation. Worth a look sometime to confirm neither holds an OAuth client or Pub/Sub configuration, since stray unverified clients cause confusion later. Not urgent and not part of this submission.
