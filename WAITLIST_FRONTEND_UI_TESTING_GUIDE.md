# Waitlist Frontend UI Testing Guide

**Last updated:** 2026-07-29
**Scope:** Browser verification of the pre-launch waitlist across the marketing site (`velvet-elves-marketing-website`) and the platform console (`velvet-elves-frontend`).
**Audience:** Jan, QA testers, and product stakeholders validating the feature in local, dev, or stage environments.

Companion documents: `MARKETING_WAITLIST_IMPLEMENTATION_PLAN.md` (what was built and why) and `FRONTEND_UI_TESTING_GUIDELINES.md` (conventions for the automated Vitest/MSW tests).

---

## 1. What This Guide Covers

The waitlist exists because sign-up is closed before launch. A visitor who would
have clicked "Create an account" now joins a list, gets a confirmation email
from hello@, and is promised two specific things: **founding pricing** and
**the demo, first**. This guide verifies all of that through the UI:

1. The **`/waitlist` page** — layout, copy, and the capture card's four states.
2. **Capture behavior** — a fresh signup, a repeat signup, the bot honeypot, and a backend that cannot be reached.
3. **CTA replacement** — every former "Create an account" button now points at the waitlist.
4. **Surfaces that must NOT have changed** — the demo modal, the newsletter strip, the FSBO/attorney early-access boxes, and Login.
5. The **hello@ confirmation email** — sent once per new waitlist signup, and never for anything else.
6. The **platform console** at `/platform/waitlist` — stat tiles, filters, search, table, pagination.
7. **CSV export** — forces a save, matches the on-screen filter.
8. **The launch-day revert** — `VITE_WAITLIST_MODE=false` restores account sign-up everywhere.
9. **Share card and SEO** for the page Jake links in ads.
10. **Responsive and accessibility** checks.

This is a frontend UI guide. It assumes the backend is running with migration
`20260920090000_marketing_waitlist.sql` applied.

---

## 2. Pre-Flight Checklist

### 2.1 Services

```powershell
# Backend (must have the waitlist migration applied)
cd c:\Projects\velvet-elves-backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000

# Marketing site — port 5182 is REQUIRED, see 2.3
cd c:\Projects\velvet-elves-marketing-website
npm run dev -- --port 5182

# App frontend (only needed for sections 9-10)
cd c:\Projects\velvet-elves-frontend
npm run dev
```

### 2.2 Confirm the migration is applied

If it is not, every waitlist submit fails with the honest error message and no
row is ever written. Quickest UI-level check: submit one signup (§5.1) and see
whether it appears in the platform console (§9). If it does not, stop and apply
the migration before continuing — everything downstream will produce false
failures.

### 2.3 Ports are not optional

| Service | Port | Why |
| --- | --- | --- |
| Backend | 8000 | Default `VITE_API_URL` for the marketing site |
| Marketing site | **5182** | The backend's default `CORS_ORIGINS` allows `localhost:5182`. On any other port the browser blocks lead capture and you will see the error state on every submit — a CORS failure that looks exactly like a broken feature. |
| App frontend | 5173 | Already in `CORS_ORIGINS` |

If you must use a different port, add it to `CORS_ORIGINS` and **restart** the
backend. The backend loads its `.env` by absolute path at startup; `--reload`
does not pick up env changes.

### 2.4 Environment expectations

1. `VITE_WAITLIST_MODE` is unset or `true` for sections 5-9. Only §11 turns it off.
2. Browser devtools console open throughout. Any red console error is a test failure unless it is a known unrelated environment warning.
3. For local testing, prefer a backend with **`SENDGRID_API_KEY` empty**. The confirmation path then logs instead of sending, which is what you want: the test addresses below do not exist, and real sends to them generate bounces that damage the sender reputation of `velvetelves.com`.
4. On stage, where a real key IS configured, use a mailbox you control (§8.3).

### 2.5 Browser matrix

| Browser | Required | Notes |
| --- | --- | --- |
| Chrome latest | Yes | Primary QA browser |
| Edge latest | Recommended | Windows parity check |
| Safari / iOS Safari | Recommended | The capture card is the one interactive element; check the field and button |
| Chrome devtools mobile viewport | Yes | Check at 390px width |

---

## 3. Role Matrix

| Surface | Anonymous visitor | Signed-in tenant user | Platform admin |
| --- | --- | --- | --- |
| `/waitlist` page and its form | Yes | Yes | Yes |
| Waitlist CTAs across the marketing site | Yes | Yes | Yes |
| `/create-account` waitlist card | Yes | Yes | Yes |
| `/platform/waitlist` console | **No** | **No** | Yes |
| Waitlist entry in the app sidebar | No | **No** | Yes |
| CSV export | No | No | Yes |

The marketing site has no login, so everything on it is public by design. The
console is the opposite: it holds captured email addresses, so a non-platform
user reaching it — or even seeing the sidebar entry — is a **P0 permissions
bug**.

---

## 4. Shared Test Data

Use unique addresses. The endpoint is idempotent per `(email, interest)`, so
reusing an address from an earlier run produces a *success* message with no new
row, and you will misread it as a broken write.

| Purpose | Suggested value |
| --- | --- |
| Fresh signup | `waitlist.test.<today><HHMM>@example.com` |
| Duplicate test | reuse the fresh signup address |
| Honeypot test | `bot.test.<today><HHMM>@example.com` |
| Offline test | `offline.test.<today><HHMM>@example.com` |
| Stage real-delivery test | a mailbox you actually control |

### 4.1 The rate limit will bite you

The public capture endpoint allows **10 submissions per IP per minute**. A
tester working through this guide quickly can trip it, and the page then shows
the same honest error as a backend outage. If submissions start failing after
roughly ten attempts, wait a minute and retry before filing a bug.

---

## 5. The `/waitlist` Page

### 5.1 Layout and copy (desktop, 1440px)

Navigate to `http://localhost:5182/waitlist`.

Expected, top to bottom:

1. Aurora/starfield hero on the light "Daybreak" background, matching the rest of the site.
2. Eyebrow: `FOUNDING MEMBER WAITLIST` with the brand spark glyph.
3. Headline: **"Get in before the doors open."** — "doors open." in the serif italic aurora gradient.
4. Lead paragraph mentioning onboarding in waves, founding pricing, and the demo.
5. A white capture card containing:
   - heading "Join the waitlist",
   - the line "Founding pricing and the demo, first. One email, nothing else.",
   - an email field (`you@email.com`) and a gradient **Join the waitlist** button,
   - three ticked promises: founding pricing locked in / the demo the moment it's ready / no spam, easy to leave.
6. Section **"What founding members get"** — three cards: Founding pricing, First look at the demo, An early invite.
7. Section **"How it goes from here"** — three numbered steps: Join the list, We send the demo, Your invite arrives.
8. Closing line: "Want to see more first? How it works · FAQ" (both links work).
9. The standard newsletter strip and site footer.

Failures to watch for:

- **A second email box in the page body** other than the capture card and the footer newsletter strip. The page must not carry a `FinaleCta` — two competing email boxes on a capture page is a design regression.
- Any promise beyond founding pricing and the demo (a discount percentage, a seat count, a launch date). The product cannot back those, so **any invented specific is a P1 copy bug.**

### 5.2 The four states of the capture card

Per `FRONTEND_UI_TESTING_GUIDELINES.md` §3, verify all four:

| State | How to reach it | Expected |
| --- | --- | --- |
| Idle | Load the page | Field empty, button reads "Join the waitlist", enabled |
| Submitting | Click submit and watch | Button reads "Sending…", field and button disabled — no double-submit possible |
| Success | §5.3 | Card is replaced by the confirmation panel |
| Error | §5.6 | Honest failure message with a mailto fallback |

### 5.3 Fresh signup

1. Enter your fresh address. Submit.
2. The card is **replaced** by a confirmation panel containing:
   - a green tick and **"You're on the list."**
   - "A confirmation from hello@velvetelves.com is on its way. Here's what happens next:"
   - two follow-up lines (We send the demo / Your invite arrives),
   - a closing line linking to *how it works* and the *contract-to-close guide*.
3. The original form is **gone**, not merely stacked above the panel. Seeing both the panel and a leftover "You're on the list." one-liner is a bug.
4. Confirm persistence through the UI in §9.2 rather than the database — the console is the supported way to see a signup.

### 5.4 Duplicate signup

Submit the **same address again** (reload the page first).

- Expected: the same success panel.
- Expected in the console (§9): still **one** row for that address, and the Confirmation column still reads "Sent" once.

This is correct behavior, not a missed write. Repeat submits must never create
duplicate rows or send a second email — otherwise the form becomes a button for
mailing someone repeatedly.

### 5.5 Honeypot (bot simulation)

1. Open devtools console on `/waitlist` and run:

   ```js
   document.querySelector('input[name="company"]').value = 'spam-bot'
   ```

2. Enter the bot address and submit.
3. Expected: the normal success panel — the bot must learn nothing.
4. Expected in the console (§9): **no row** for that address.

A hidden `company` field that is visible on screen, reachable by keyboard
tabbing, or announced by a screen reader is a bug.

### 5.6 Backend unreachable

1. Stop the backend (or block the request in devtools → Network → block request URL for `*/marketing/leads`).
2. Submit the offline address.
3. Expected message: **"That didn't go through. Email us at hello@velvetelves.com and we'll take it from there."** with `hello@velvetelves.com` as a working `mailto:` link.
4. Expected: no crash, no blank page, and the form remains usable for a retry.

A spinner that never resolves, or a success panel shown when nothing was saved,
is a **P1** — it silently loses a lead.

### 5.7 Mobile (390px)

1. Devtools → mobile viewport at 390px.
2. Expected: no horizontal page scroll at any scroll position.
3. Expected: the email field and the submit button **stack vertically** and are each roughly 48px tall.
4. **Specifically measure the email field.** A previous defect collapsed it to about 21px on mobile while desktop looked correct. In devtools, select the field and confirm its computed height is ~48px. A short, hard-to-tap field is a P1 on the page ad traffic lands on.
5. Repeat this check on the newsletter strip at the bottom of any page and inside the demo modal — they share the same component.

---

## 6. CTA Replacement Sweep

With waitlist mode ON, walk these pages. On each, the former account button must
read **"Join the waitlist"** and route to `/waitlist`.

| Page | Where to look | Expected |
| --- | --- | --- |
| `/` | Hero, beside "Watch demo" | Outline "Join the waitlist" |
| `/` | Bottom call-to-action band | Quiet "Join the waitlist" |
| `/pricing` | Both pricing cards | "Join the waitlist" |
| `/pricing` | Intro copy under "The fee" | Mentions joining the waitlist for founding pricing |
| `/features` | Hero, beside "Watch demo" | "Join the waitlist" |
| `/demo` | Under the demo email box | "Or join the founding-member waitlist:" then the button |
| `/agents` | Hero | "Join the waitlist" |
| `/brokers-teams` | Hero | "Join the waitlist" |
| Header (desktop) | Beside "Pricing" | A quiet "Waitlist" link |
| Header (mobile) | Open the menu | "Join the waitlist" button above "Login" |
| Footer | Product column | "Waitlist" link |

### 6.1 The zero-stragglers check

On each page above, open devtools console and run:

```js
[...document.querySelectorAll('a')]
  .filter(a => a.href.includes('/register'))
  .map(a => a.textContent.trim())
```

Expected result: **an empty array on every page.** A single straggler pointing
at the app's register screen defeats the purpose — Jake asked for sign-up to be
replaced while the product is pre-launch.

### 6.2 `/create-account`

The route stays alive so old links and printed materials keep working.

1. Visit `/create-account`.
2. Expected: eyebrow "Founding member waitlist", headline **"We're onboarding in waves."**, and an inline waitlist email capture.
3. Expected: a small **"Already invited? Continue to the app"** link that still opens the app's register screen in a new tab.
4. That invited link is deliberate and must NOT be removed — existing testers and invited users still need a way in.

---

## 7. Surfaces That Must Not Have Changed

Regression checks. Each of these serves a different promise and was deliberately
left alone.

| Surface | Where | Expected |
| --- | --- | --- |
| Demo modal | Click "Watch demo" anywhere | Still says the demo is being finished; its box still submits the **demo** list, not the waitlist |
| Newsletter strip | Above the footer, every page | Still "Stay in the loop." with a **Subscribe** button |
| FSBO early access | `/fsbo`, bottom | Still "Want in early?" with **Request invite** |
| Attorneys / Client portal | Bottom of each | Same early-access capture, unchanged |
| Login | Header, and mobile menu | Still points at the app; never replaced by the waitlist |

### 7.1 Verifying the demo modal submits the right list

The home page contains both the footer newsletter form and the modal's form. To
check the modal specifically, open it, then run in the console:

```js
document.querySelector('[role="dialog"] input[type="email"]')
```

That must return the modal's field (not `null`). Submit through the modal, then
confirm in the console (§9) that the new row's **Type** column reads **Demo**,
not Waitlist. A demo signup landing in the waitlist segment would corrupt the
list Jake markets against.

---

## 8. The Confirmation Email

### 8.1 What is promised

| Property | Expected |
| --- | --- |
| From | `Velvet Elves <hello@velvetelves.com>` |
| Reply-to | `hello@velvetelves.com` (monitored — replies must reach a person) |
| Subject | `You're on the Velvet Elves waitlist` |
| Sent for | **waitlist signups only** |
| Sent how often | **Exactly once per address, ever** |

### 8.2 UI-only verification (local/dev)

You do not need an inbox to check the wiring:

1. Complete a fresh signup (§5.3).
2. Open `/platform/waitlist` (§9) and find the row.
3. The **Confirmation** column must read **"Sent"** with a mail tick.
4. Submit the same address again; the column must still show one row, still "Sent".
5. Sign up for the **newsletter** (footer strip) and for the **demo** (modal). Their rows must show **"—"** in the Confirmation column — those lists promise no follow-up mail, so sending one would be spam.

### 8.3 Real delivery (stage only)

Local runs should have SendGrid disabled (§2.4), so nothing is actually sent.
On stage, with a real key:

1. Sign up with a mailbox you control.
2. Confirm the email arrives, from `hello@`, with the subject above.
3. Confirm the body promises **only** founding pricing, the demo first, and an early invite.
4. Confirm the **"See how it works"** button opens the marketing site — **not** the app. The recipient has no account, so an app link would be a login wall.
5. Confirm the footer carries the "Reply to this email if you'd like off the list" line.
6. Confirm the plain-text version reads correctly (view source / disable HTML in your client).

---

## 9. Platform Console (`/platform/waitlist`)

### 9.1 Access and navigation

1. Sign in to the app as a **platform admin**.
2. Sidebar → **Platform** group → **Waitlist** (mail icon). Confirm the entry exists.
3. The page opens with breadcrumb **Platform › Waitlist**, the serif title **Waitlist**, and an "N total" badge.
4. Sign in as a normal tenant user: the sidebar entry must be **absent**, and typing `/platform/waitlist` directly must not render the console.
5. Signed out, `/platform/waitlist` must land on login.

Any leak here is **P0** — this page lists captured email addresses.

### 9.2 Stat tiles and table

Expected tiles: **Waitlist**, **Demo list**, **Newsletter**, **Early access**,
each with a count and a one-line description. Segments with no signups show
`0`, not a blank or a missing tile.

Expected table columns:

| Column | Content |
| --- | --- |
| Email | The captured address |
| Type | A badge: Waitlist / Demo / Newsletter / Early access |
| Signed up from | The page it came from (e.g. `/waitlist`), plus "via …" referrer when known |
| Confirmation | "Sent" for mailed waitlist rows; "Not sent" for an unmailed waitlist row; "—" for other segments |
| Signed up | Absolute date plus a relative age ("21m ago") |

Newest signup first. Verify by making a new signup and refreshing — it must
appear at the top.

### 9.3 Filters, search, pagination

1. The segment filter defaults to **Waitlist** — that is what the page is for.
2. Switch to **Demo**: only demo rows remain. Switch to **All**: everything appears.
3. **The stat tiles must not change** when you filter. They always describe the whole table; only the table and the "Showing X–Y of Z" line follow the filter.
4. Type a partial address into search; the table narrows. Search for something absent; expect **"No signups match ..."**, not an empty box.
5. Clear the search; the full list returns.
6. Changing a filter must return you to page 1. If you are on page 2 and filter down to a handful of rows, an empty table with "Page 2 / 1" is a bug.
7. With no signups at all, expect the honest empty state: "No signups yet. The waitlist is live at velvetelves.com/waitlist."

### 9.4 Refresh

Click **Refresh**; a spinner appears briefly and counts update. Add a signup
from another browser tab, click Refresh, and confirm it appears.

---

## 10. CSV Export

1. With the segment filter on **Waitlist**, click **CSV**.
2. Expected: the file downloads directly — **the page must not navigate away**, and no new tab may open. Confirm the URL in the address bar is unchanged.
3. Expected filename: `waitlist-YYYY-MM-DD.csv` (today's date). With the filter on **All**, `marketing-leads-YYYY-MM-DD.csv`.
4. Expected toast: "Exported N signups."
5. Open the file. The header must be exactly:

   ```text
   email,interest,source_page,referrer,signed_up_at,confirmation_email_sent_at
   ```

6. Expected contents: **the filtered rows, not the whole table** — filter to Waitlist and the file must contain only waitlist rows.
7. Expected: **all matching rows, not just the visible page.** If there are more than 100 signups, the file must still contain every one.
8. Apply a search term and export again; the file must respect the search too.
9. With zero matching rows the CSV button is disabled.

> **Test this by hand in a normal browser.** Automated/headless browsers on the
> current dev machine cancel every in-memory (`blob:`) download, so an automated
> CSV check will report a missing file even when the feature works. The file
> actually landing on disk is the one step that must be confirmed manually.

---

## 11. Launch-Day Revert (`VITE_WAITLIST_MODE=false`)

Jake asked for the waitlist "for now, until we get our task list up and
running", so the revert must be verified before shipping — not discovered on
launch day.

```powershell
cd c:\Projects\velvet-elves-marketing-website
$env:VITE_WAITLIST_MODE = "false"
npm run dev -- --port 5182
```

| Check | Expected |
| --- | --- |
| Every page in §6 | Buttons read **"Create an account"** again and point at the app's register screen |
| "Join the waitlist" buttons | **Zero** anywhere on the site |
| Header and footer | The "Waitlist" link is gone |
| `/waitlist` | **Still loads and still works** — old ad links must not 404 |
| `/create-account` | Back to "Start with Velvet Elves." with "Continue to the app" |
| `/pricing` intro copy | Back to the account wording |

Re-run the §6.1 console snippet inverted: every page should now return a
non-empty array of register links.

Remember to clear the variable (`Remove-Item Env:VITE_WAITLIST_MODE`) before
resuming normal testing.

---

## 12. SEO and Share Card

The waitlist page is what Jake links in ads and posts, so its preview matters.

1. View source on `/waitlist` (or check the built `dist/waitlist.html`).
2. Expected `<title>`: "Join the Velvet Elves waitlist".
3. Expected meta description mentioning founding pricing and the demo.
4. Expected canonical: `https://velvetelves.com/waitlist`.
5. Expected `og:image` pointing at `/og/waitlist.png`, and that image must load (not 404).
6. The page must **not** carry `noindex`.
7. After a production build, `sitemap.xml` must contain `/waitlist` (17 URLs total).
8. Paste the URL into Slack or LinkedIn's post composer and confirm the card renders with the branded image.

---

## 13. Responsive and Accessibility Checks

1. **Keyboard only:** Tab to the email field, type, press Enter. The form submits without a mouse.
2. **Focus visibility:** The field and button show a clear focus ring.
3. **Honeypot invisibility:** Tabbing must never land on the hidden `company` field.
4. **Screen reader labels:** The email input exposes an "Email address" label. The submit button's text is meaningful on its own — never a bare icon.
5. **Error announcement:** The failure message in §5.6 is announced (it carries an alert role), not merely shown.
6. **Contrast:** Orange gradient button text stays legible; ticked promise text is readable against the card.
7. **Viewports:** 390px, 768px, 1024px, 1440px, 1920px — no horizontal scroll, no overlap, no clipped text.
8. **Reduced motion:** With OS "reduce motion" enabled, the hero's animated elements settle rather than looping. The page must remain fully readable with no JavaScript animation running.
9. **Console tab:** Console error count must be zero across the run.

---

## 14. Automated UI Test Recommendations

Following `FRONTEND_UI_TESTING_GUIDELINES.md` (Vitest + MSW + Testing Library),
the highest-value tests to add:

1. `EmailCapture` — all four states, with MSW returning success then failure; assert the honest error text and mailto, and that the submit button disables while in flight.
2. `EmailCapture` — `onSuccess` callback path renders nothing itself (so a caller-owned panel is not doubled up).
3. `AccountCta` — renders the waitlist route and label when the flag is on, and the register URL and label when off. This is the single point every CTA resolves through, so one test covers all eight surfaces.
4. `WaitlistPage` — success panel replaces the form and mentions the hello@ sender.
5. `PlatformWaitlistPage` — loading / error / empty / populated; the "Confirmation" column showing "Sent" vs "—" by segment; and that the stat tiles do not change when the filter changes.
6. CSV builder — pure-function test over the row-to-CSV mapping: header exactly as specified, quotes escaped, `null` referrer rendered as an empty quoted field.

Do not assert Tailwind class strings as a proxy for appearance. The mobile
field-height defect from §5.7 is the exception that proves the rule: catch that
one with a computed-height assertion in a real browser, not a class check.

---

## 15. Smoke Test Script (10 minutes)

For a quick pass after any deploy:

1. `/waitlist` loads with the correct headline and capture card.
2. A fresh address submits and shows the success panel.
3. The signup appears in `/platform/waitlist` with Confirmation "Sent".
4. The same address submitted again creates no second row.
5. The home page hero button reads "Join the waitlist" and lands on `/waitlist`.
6. No page in §6 links to `/register` except `/create-account`'s "Already invited?" link.
7. The demo modal still submits to the Demo list.
8. CSV downloads, opens, and contains the new signup.
9. 390px viewport: no horizontal scroll and a full-height email field.
10. Console is free of errors.

---

## 16. Bug Report Template

```text
Feature area:      (waitlist page / CTA sweep / confirmation email / console / CSV / revert)
Environment:       (local / dev / stage)
Waitlist mode:     (on / off)
Browser:
Viewport:
Email address used:
Steps to reproduce:
Expected:
Actual:
Screenshot/video:
Console error:
Network response, if relevant:
Severity:
```

| Severity | Meaning |
| --- | --- |
| P0 | Captured email addresses exposed to a non-platform user; an address mailed repeatedly; a signup silently lost while showing success |
| P1 | Cannot join the waitlist; a CTA still routes to sign-up; the confirmation never sends; CSV exports the wrong rows; the mobile field is untappable |
| P2 | Wrong badge or count, filter/pagination glitch, partial responsive break, export filename wrong |
| P3 | Copy, spacing, visual polish, non-blocking annoyance |

---

## 17. Final Acceptance Criteria

The waitlist frontend is ready when:

1. `/waitlist` renders correctly on desktop and mobile and promises only founding pricing and the demo.
2. A fresh signup succeeds, persists, and is visible in the platform console.
3. A repeat signup never creates a second row and never sends a second email.
4. The honeypot absorbs bots silently and stores nothing.
5. An unreachable backend produces an honest error with a working mailto fallback — never a false success.
6. No marketing page links to the app's register screen except the deliberate "Already invited?" link.
7. The demo modal, newsletter strip, early-access captures, and Login are unchanged.
8. Confirmation status is visible per row, and only waitlist rows ever show one.
9. The console is reachable by platform admins only, with working filters, search, and pagination.
10. CSV export forces a save, respects the active filter, and includes every matching row.
11. `VITE_WAITLIST_MODE=false` restores account sign-up everywhere while `/waitlist` stays reachable.
12. The share card and sitemap entry are correct for the page used in advertising.
13. Keyboard, screen-reader, and reduced-motion paths all work, with a clean console.
