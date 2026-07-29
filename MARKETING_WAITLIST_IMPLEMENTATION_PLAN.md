# Marketing Site Waitlist: Implementation Plan

Date: 2026-07-29
Author: Jan (with Claude)
Status: **IMPLEMENTED 2026-07-29** and verified in a real browser (§11 records the run).
Uncommitted — Jan commits.

---

## 1. What Jake asked for (email thread analysis)

Thread: "Waitlist on Marketing Site".

Jake's opening request:
> "I am getting some marketing going to start building our waitlist for launch, but there isn't a way to sign up for the waitlist. Think you can add something there for us?"

My reply committed to three things and asked three questions. Jake's answers resolve every open decision:

| # | Decision point | Jake's answer | Requirement |
|---|---|---|---|
| R1 | What the signup promises | "Let's give them founding pricing and the demo" | The waitlist CTA and page promise founding pricing + the demo, and nothing we cannot deliver |
| R2 | Confirmation email | "Please do set up the auto email from Hello@" | Every new waitlist signup gets an automatic confirmation email from hello@velvetelves.com |
| R3 | Create-account buttons | "If we can replace the create an account button for now until we get our task list up and running that would be great!" | Every "Create an account" CTA on the marketing site becomes a waitlist CTA, and the change must be easy to revert at launch ("for now") |
| R4 | Home page signup | My commitment, accepted by Jake | A proper "Join the waitlist" signup on the home page |
| R5 | Dedicated page | My commitment, accepted by Jake | A `/waitlist` page Jake can link in ads and posts |
| R6 | Admin visibility | My commitment ("signups are saved, but nothing displays them"), accepted by Jake | A waitlist view with CSV export so Jake can actually see and use the list |

Two things Jake did NOT ask to change, so they stay:
- "Login" links stay. Existing users (Jake, Audri, testers) still need to reach the app.
- The demo modal ("we'll send the demo when it's ready", interest `demo_waitlist`) stays. It serves a different promise and already works.

---

## 2. Current state (audited 2026-07-29)

### 2.1 What already exists and gets reused

- **Capture pipeline, end to end.** `EmailCapture` (`velvet-elves-marketing-website/src/components/ui/EmailCapture.tsx`) POSTs via `submitLead` (`src/lib/api.ts`) to the public no-auth endpoint `POST /api/v1/public/marketing/leads` (`velvet-elves-backend/app/api/v1/public_marketing.py`). Honeypot field, rate limit (10/min/IP), idempotent duplicate handling, honest error fallback to `CONTACT_EMAIL`. This is the component and endpoint the waitlist builds on.
- **`marketing_leads` table** (migration `20260902090000_marketing_leads.sql`): platform-global, service-role RLS, unique index on `(lower(email), interest)`, `interest` CHECK constraint currently allowing `demo_waitlist | newsletter | early_access`.
- **hello@ sending infrastructure.** `email_senders.py` resolves `EmailPurpose.WELCOME` to hello@velvetelves.com (domain-authenticated in SendGrid, replies monitored). `welcome_email_service.py` has the full house pattern: branded HTML shell (`_shell`, `_p`, `_signoff`), text + HTML bodies, async httpx to SendGrid v3, fire-and-forget with strong task references, "no key → log instead of send", atomic one-time claim so nothing double-sends.
- **Platform admin surface.** `PlatformAdminGuard` route group in the app frontend (`App.tsx` ~line 888), `ROUTES.PLATFORM_*` constants, sidebar links in `AppLayout.tsx` ~line 465, backend `require_platform_admin` dependency (`platform_tenants.py` pattern). Client-side CSV export via blob + forced `<a download>` already exists twice (`PlatformCostsPage.tsx:364`, `PlatformAIUsagePage.tsx:222`) and is the house rule.
- **Design system.** Daybreak (white + lavender/aurora): `bg-night` tokens (holding light values), `Aurora`/`Starfield` fx, `Eyebrow`, `Button` (variants `primary`/`outline`/`ghost`/`ghost-light`), `font-display`/serif-italic gradient accent words, rounded-3xl white cards with `shadow-premium`. The waitlist page composes from these; nothing new is invented.

### 2.2 What is missing

- No `waitlist` interest value (schema Literal, DB CHECK, frontend type).
- No confirmation email of any kind for marketing leads (R2).
- No `/waitlist` page, no waitlist CTA anywhere (R4, R5).
- No screen anywhere that displays `marketing_leads`; the repository has only `find` and `create`, and there is no platform API for leads (R6).

### 2.3 Complete inventory of "Create an account" surfaces (R3)

Every place the marketing site links `REGISTER_URL` (the live app's /register):

| File | Location | Current CTA |
|---|---|---|
| `src/components/home/Hero.tsx:106` | Home hero, secondary button | outline "Create an account" |
| `src/components/role/RoleHero.tsx:34` | Agents + Brokers/Teams heroes (`account='create'`) | outline "Create an account" |
| `src/components/sections/FinaleCta.tsx:41` | Bottom of every page with `account='create'` | ghost "Create an account" |
| `src/pages/PricingPage.tsx:163,199` | Pricing cards | primary/outline buttons to /register |
| `src/pages/PricingPage.tsx:128` | Copy: "Create an account and your first deal is free either way." | prose |
| `src/pages/FeaturesPage.tsx:99` | Features closing band | ghost-light "Create an account" |
| `src/pages/DemoPage.tsx:47` | Demo page | ghost-light button to /register |
| `src/pages/CreateAccountPage.tsx` | The /create-account trampoline page itself | primary "Continue to the app" |

Not affected: `Nav.tsx` (has only Login + Watch demo), `MobileSheet.tsx` (only Login), `Footer.tsx` (no account links), and the `account='early-access'` variants on FSBO/Attorney/Client pages (those already capture email instead of registering, exactly because those roles cannot self-serve).

---

## 3. Design decisions

### D1. New `waitlist` interest value, not a reuse of `early_access`

Jake will market against this list and the CSV he exports must mean "people promised founding pricing and the demo". `early_access` already carries a different promise (roles that cannot self-sign-up yet) and has existing rows. Mixing them would muddy both. So: add `waitlist` to the Literal, the DB CHECK constraint, and the marketing site type. The unique index `(lower(email), interest)` keeps waitlist signups idempotent independently of any newsletter/demo signup by the same address, which is correct: someone on the newsletter should still be able to join the waitlist.

### D2. One `WAITLIST_MODE` flag makes R3 reversible

Jake said "for now until we get our task list up and running". Instead of scattering edits that need reverse surgery at launch, every CTA swap branches on a single exported constant:

```ts
// src/lib/config.ts
/** Pre-launch: waitlist replaces "Create an account" everywhere (Jake, 2026-07). Set VITE_WAITLIST_MODE=false at launch to restore account CTAs. */
export const WAITLIST_MODE = import.meta.env.VITE_WAITLIST_MODE !== 'false'
export const WAITLIST_PATH = '/waitlist'
```

Launch day is one env change + redeploy; every button reverts to `REGISTER_URL` at once.

### D3. Confirmation email rides the existing welcome infrastructure

New module `app/services/marketing_waitlist_email.py` reusing `welcome_email_service`'s render helpers (`_shell`, `_p`, `_signoff`) and delivery posture, sent as `EmailPurpose.WELCOME` (hello@, monitored, replies welcome, exactly what Jake asked). Send is fire-and-forget after the lead row is created: a failed email must never fail the signup, matching the account-welcome rule. Only a genuinely new row triggers a send; the idempotent duplicate path and the honeypot path send nothing, so the endpoint cannot be used to spam an address by resubmitting it. A `confirmation_email_sent_at` column on `marketing_leads` records the send (and backstops exactly-once with the same atomic-claim UPDATE pattern as `users.welcome_email_sent_at`).

Compliance note: because the email promises future sends (the demo, the founding invite), the footer carries an honest opt-out line ("Reply to this email if you'd like off the list") in addition to the "why you got this" line. We have no unsubscribe-list infrastructure yet; replies land in the monitored hello@ inbox, which is workable at waitlist volume. Flagged in §10 as a thing to revisit before large-scale sends.

### D4. Admin view lives at /platform/waitlist

The list is platform-global (no tenant), so it belongs in the platform-admin group next to Tenants/Costs/Billing, guarded by `require_platform_admin` on the API and `PlatformAdminGuard` on the route. Jake's account is a platform admin, so he sees it in his sidebar. CSV export follows the established client-side blob + forced-download pattern (house rule: download buttons must force save, never navigate).

### D5. What deliberately does NOT change

- Demo modal and its `demo_waitlist` interest: untouched (different promise, already correct).
- `account='early-access'` captures on FSBO/Attorney/Client pages: untouched (different promise; Jake only asked about create-account buttons).
- Nav CTA hierarchy: "Watch demo" stays the gradient primary, Login stays quiet. The waitlist gets a flat "Waitlist" link beside Pricing plus a primary button in the mobile sheet. Option for Jake (non-blocking): make "Join the waitlist" the nav's gradient CTA instead of "Watch demo" while in waitlist mode. I default to the minimal change; happy to flip it if Jake prefers.
- Newsletter strip above the footer stays a newsletter signup. Two different email promises stacked at the bottom of the same page would compete; the finale CTA right above it already carries the waitlist. Reversible later if Jake wants the strip repurposed.

---

## 4. Backend changes

### 4.1 Migration `20260920090000_marketing_waitlist.sql` (next free slot)

```sql
BEGIN;
-- Widen the interest domain with the launch waitlist segment.
ALTER TABLE public.marketing_leads DROP CONSTRAINT IF EXISTS marketing_leads_interest_check;
ALTER TABLE public.marketing_leads ADD CONSTRAINT marketing_leads_interest_check
    CHECK (interest IN ('demo_waitlist', 'newsletter', 'early_access', 'waitlist'));
-- One-time confirmation-email claim (same pattern as users.welcome_email_sent_at).
ALTER TABLE public.marketing_leads ADD COLUMN IF NOT EXISTS confirmation_email_sent_at TIMESTAMPTZ;
COMMIT;
```

(Verify the auto-generated CHECK constraint name against the stage DB before finalizing; the inline CHECK from `20260902090000` should be `marketing_leads_interest_check`, with `\d marketing_leads` as the check.)

### 4.2 Schema + model

- `app/schemas/marketing.py`: `Interest = Literal["demo_waitlist", "newsletter", "early_access", "waitlist"]`; update the docstring comment.
- `app/models/marketing_lead.py`: extend the interest comment; add `confirmation_email_sent_at: datetime | None = None`.
- `app/repositories/marketing_lead_repository.py`:
  - map the new column in `_row_to_lead`;
  - add `list(*, interest: str | None, search: str | None, limit: int, offset: int) -> tuple[list[MarketingLead], int]` (ordered `created_at DESC`, `ilike` on email for search, exact count via Supabase `count="exact"`);
  - add `counts_by_interest() -> dict[str, int]`;
  - add `claim_confirmation(lead_id) -> bool` (`UPDATE ... SET confirmation_email_sent_at = now() WHERE id = :id AND confirmation_email_sent_at IS NULL`, returns whether the claim won).

### 4.3 Confirmation email: `app/services/marketing_waitlist_email.py`

- `render_waitlist_confirmation_html/text()` using the shared shell (import `_shell`, `_p`, `_signoff` from `welcome_email_service`; if importing privates feels wrong during implementation, lift the three helpers into a tiny shared `platform_email_rendering.py` and have both modules use it).
- `schedule_waitlist_confirmation(supabase, lead)`: claim via `claim_confirmation`, then fire-and-forget `_deliver` (same SendGrid v3 httpx call, `sender_for(EmailPurpose.WELCOME)`, no-key → log line, never raises). No `communication_logs` row: that table requires a `tenant_id` and leads predate any tenant; `confirmation_email_sent_at` is the send record.
- Copy: §8. CTA button links to `https://velvetelves.com/waitlist` (site URL from a new `marketing_site_url` setting, default `https://velvetelves.com`), NOT the app, because the recipient has no account.

### 4.4 Endpoint change: `public_marketing.py`

In `capture_lead`, after the `repo.create(...)` call only (not the honeypot return, not the idempotent-duplicate return):

```python
if payload.interest == "waitlist":
    await schedule_waitlist_confirmation(supabase, lead)  # claim awaited, send fire-and-forget
```

The existing rate limiter (10/min/IP) already bounds abuse of the email path; the unique index bounds it to one email per address ever.

### 4.5 Platform API: new `app/api/v1/platform_marketing.py`

Modeled on `platform_tenants.py` (router prefix `/platform/marketing-leads`, tag `platform`, every path `Depends(require_platform_admin)`), registered in the API router next to the other platform modules.

- `GET /platform/marketing-leads?interest=&search=&limit=&offset=` → `{ items: [...], total: int, counts: {waitlist: n, demo_waitlist: n, newsletter: n, early_access: n} }`. `limit` capped at 1000, default 100. Item shape: `id, email, interest, source_page, referrer, created_at, confirmation_email_sent_at` (no user_agent in the list payload; it stays queryable in the DB).
- Response schemas in `app/schemas/marketing.py` (`PlatformMarketingLeadItem`, `PlatformMarketingLeadsResponse`).
- No export endpoint: CSV is generated client-side per the established pattern; the page fetches all matching rows (waitlist volumes are small) with the 1000-cap pagination loop.

### 4.6 Backend tests

Extend `app/tests/test_public_marketing_api.py`:
- `waitlist` interest accepted and persisted.
- New waitlist signup schedules exactly one confirmation (monkeypatch the deliver coroutine; assert called once with the right recipient).
- Duplicate waitlist signup: 200 ok, deliver NOT called again.
- Honeypot submit: 200 ok, no row, no send.
- Other interests (`newsletter`): no confirmation send.

New `app/tests/test_platform_marketing_api.py` (modeled on the existing platform tests): 401/403 for anonymous and non-platform users, listing with interest filter + search, counts shape.

---

## 5. Marketing site changes

### 5.1 Shared plumbing

- `src/lib/config.ts`: add `WAITLIST_MODE`, `WAITLIST_PATH` (§3 D2).
- `src/lib/api.ts`: `LeadInterest` union gains `'waitlist'`.
- `src/components/ui/EmailCapture.tsx`:
  - `Interest` union gains `'waitlist'`; `SUBMIT_LABEL.waitlist = 'Join the waitlist'`.
  - New optional `onSuccess?: () => void` prop so the waitlist page can swap in its full success panel (the small inline "You're on the list." stays the default for all existing call sites).
- `.env` / `.env.example`: document `VITE_WAITLIST_MODE`.

### 5.2 New page: `src/pages/WaitlistPage.tsx` at `/waitlist`

Composed entirely from existing primitives so it reads as native Daybreak. Structure top to bottom:

1. **Hero band**: `bg-night` + `Aurora variant="hero"` + `Starfield`, `Eyebrow mark` "Founding member waitlist", display headline with the serif-italic gradient accent (copy §9), lead paragraph naming both promises (founding pricing, demo first).
2. **Signup card** (the centerpiece, directly under the headline): rounded-3xl white card, `shadow-premium`, containing the `EmailCapture interest="waitlist" sourcePage="/waitlist"` and three trust bullets (lucide `Check`): "Founding pricing, locked in", "The demo, the moment it's ready", "No spam, and easy to leave".
3. **Success state** (via `onSuccess`): the card swaps to a confirmation panel: `CheckCircle2`, "You're on the list.", "what happens next" as three short lines (confirmation email from hello@ is on its way / demo lands in your inbox first / founding-pricing invite when doors open), plus quiet links to the guide and FAQ so the visit continues.
4. **"What founding members get"**: three-card grid (icons `BadgePercent`, `PlayCircle`, `KeyRound`): Founding pricing, First look at the demo, Early access invite. Short honest descriptions; no invented numbers (pricing page owns numbers).
5. **How it works strip**: three numbered mini-steps (Join → We send the demo → Your invite arrives), same visual language as the home page's step patterns.
6. **Quiet closer**: single line + link to `/how-it-works` and `/faq`. Deliberately NO `FinaleCta` here: this page IS the capture; a second email box or a demo-modal CTA under it would compete with itself.

SEO: `<Seo title="Join the Velvet Elves waitlist" description="Founding pricing and the first demo, reserved for the waitlist." path="/waitlist" />`, indexable.

### 5.3 Routing + SEO plumbing

- `src/routes.tsx`: add `{ path: 'waitlist', element: <WaitlistPage /> }` (vite-react-ssg prerenders it automatically).
- `scripts/gen-seo.mjs`: add `{ path: '/waitlist', priority: '0.9' }` to `ROUTES` (sitemap grows to 17 URLs); robots.txt unchanged (`/create-account` stays disallowed).

### 5.4 CTA replacement map (all behind `WAITLIST_MODE`)

| Surface | Waitlist-mode rendering |
|---|---|
| `Hero.tsx` home hero | outline button "Join the waitlist" → `/waitlist` (WatchDemoButton stays primary) |
| `RoleHero.tsx` (`account='create'`) | outline "Join the waitlist" → `/waitlist` |
| `FinaleCta.tsx` (`account='create'`) | ghost "Join the waitlist" → `/waitlist`; the `early-access` variant is untouched |
| `PricingPage.tsx` both card buttons | "Join the waitlist" → `/waitlist`; line-128 copy becomes "Join the waitlist for founding pricing, and your first deal is free either way." |
| `FeaturesPage.tsx:99` | ghost-light "Join the waitlist" → `/waitlist` |
| `DemoPage.tsx:47` | ghost-light "Join the waitlist" → `/waitlist` |
| `CreateAccountPage.tsx` | card repurposed: "We're onboarding in waves." + inline `EmailCapture interest="waitlist"`, with a small "Already invited? Continue to the app" link keeping `REGISTER_URL` alive for invited users. Route and noindex stay (old links keep working) |
| `nav.ts` `NAV_LINKS` | add `{ label: 'Waitlist', href: '/waitlist' }` beside Pricing (flat link; footer Product column gains the same link) |
| `MobileSheet.tsx` | primary "Join the waitlist" button above the existing Login button |

Implementation detail: rather than sprinkling ternaries, each swap point renders through one tiny shared component, `src/components/ui/AccountCta.tsx`, that takes the visual props (`variant`, `size`, `className`) and internally resolves `WAITLIST_MODE ? (/waitlist, "Join the waitlist") : (REGISTER_URL, "Create an account")`. One file to read, one flag to flip, zero drift between surfaces.

### 5.5 Home page (R4)

The home page gets the waitlist three ways without adding clutter: the hero's secondary CTA (above the fold), the finale CTA at the bottom, and the nav link. All route to `/waitlist` where the single capture lives. This follows the site's existing conversion pattern (CTAs funnel to one action surface) instead of embedding a second email form mid-page to fight the newsletter strip.

---

## 6. Platform admin view (app frontend)

### 6.1 Route + nav

- `src/utils/constants.ts`: `PLATFORM_WAITLIST: '/platform/waitlist'`.
- `App.tsx`: route inside the `PlatformAdminGuard` group → `PlatformWaitlistPage`.
- `AppLayout.tsx` (~line 465, platform links block): `{ to: ROUTES.PLATFORM_WAITLIST, icon: MailPlus, label: 'Waitlist' }` (lucide icon, per the no-emoji rule).

### 6.2 `src/pages/platform/PlatformWaitlistPage.tsx`

Modeled on `PlatformTenantsPage` / `PlatformCostsPage` (table + modern selectors, controls row above the list, no intro prose):

- **Stat tiles**: Total signups, Waitlist, Demo list, Newsletter, Early access (from the `counts` payload).
- **Controls row**: interest filter (Radix Select, default "Waitlist" since that is what Jake came for, with "All" available), search-by-email input, and the CSV export button on the right.
- **Table**: Email, Interest (badge), Source page, Referrer (truncated, title-attr full), Signed up (absolute date + relative), Confirmation ("Sent" tick when `confirmation_email_sent_at` is set, em-dash otherwise; only meaningful for waitlist rows). Server-side pagination, 100/page.
- **CSV export**: fetches ALL rows matching the current filter (paged 1000s), builds `email,interest,source_page,referrer,created_at,confirmation_email_sent_at`, downloads as `waitlist-YYYY-MM-DD.csv` via blob + `<a download>` + revoke (house pattern, forced save).
- **Empty state**: honest ("No signups yet. The waitlist is live at velvetelves.com/waitlist."), no demo data.

### 6.3 Data hook

`src/hooks/usePlatformMarketingLeads.ts` mirroring `usePlatformTenants.ts`: query key `['platform', 'marketing-leads', filters]`, fetch wrapper against `/api/v1/platform/marketing-leads`.

---

## 7. Confirmation email (R2): draft for Jake's sign-off

- From: Velvet Elves \<hello@velvetelves.com\> (reply-to hello@, monitored)
- Subject: **You're on the Velvet Elves waitlist**
- Preheader: Founding pricing is locked in, and the demo comes to you first.

Body (rendered in the branded shell: serif "Velvet Elves" wordmark, white 600px card, orange accent edge; text version mirrors it):

> Hello,
>
> You're on the list. Thanks for wanting in early, we're glad you're here.
>
> Here's what being on the waitlist gets you:
>
> - **Founding pricing.** When we open the doors, you get our founding-member rate, locked in.
> - **The demo, first.** We're putting the finishing touches on it. The moment it's ready, it lands in this inbox.
> - **Early access.** Waitlist members are invited in waves before the public launch.
>
> [See how it works] (button → https://velvetelves.com/how-it-works)
>
> If you have any questions, just reply to this email. A real person reads these.
>
> Thank you,
> The Velvet Elves Team

Footer line: "You're receiving this one-time confirmation because this address joined the waitlist at velvetelves.com. Reply to this email if you'd like off the list."

## 8. Waitlist page copy: draft for Jake's sign-off

- Eyebrow: FOUNDING MEMBER WAITLIST
- H1: "Get in before the *doors open.*" (accent phrase in the serif-italic aurora gradient)
- Lead: "We're onboarding in waves. Join the waitlist and you lock in founding pricing, and the demo lands in your inbox the moment it's ready."
- Card bullets: "Founding pricing, locked in" / "The demo, the moment it's ready" / "No spam, and easy to leave"
- Success panel: "You're on the list." + "A confirmation from hello@velvetelves.com is on its way. The demo comes to you first, and your founding-member invite follows when the doors open."

Both drafts promise only what R1 established: founding pricing and the demo. No invented discounts, dates, or seat counts.

---

## 9. Verification plan (run after implementation, before telling Jake)

### 9.1 Static + unit

1. Backend: `pytest app/tests/test_public_marketing_api.py app/tests/test_platform_marketing_api.py app/tests/test_email_senders.py` green.
2. Marketing site: `npm run build` green (this runs `tsc --noEmit` AND the SSG prerender, so a broken /waitlist route fails the build; never verify the typecheck through a pipe). Confirm `[gen-seo] wrote sitemap.xml (17 urls)` and that `dist/waitlist/index.html` exists with the real headline (SSG output, not an empty shell).
3. App frontend: `npm run build` green.

### 9.2 Real-browser E2E (headless Chrome via the established puppeteer-core setup)

Environment: fresh backend `uvicorn` on **:8001** (the :8000 instance goes stale; backend `.env` loads by absolute path, restart to apply), marketing site `npm run dev -- --port 5182` with `VITE_API_URL=http://localhost:8001` (5182 is already in the backend's default CORS origins; add `http://localhost:5182` to the :8001 instance's CORS env if overridden), app frontend on :5173. Drive `localhost`, not `127.0.0.1`.

| # | Check | Pass criterion |
|---|---|---|
| 1 | `/waitlist` renders (1440px) | Hero, capture card, benefit cards present; screenshot reviewed against the Daybreak look |
| 2 | `/waitlist` mobile (390px) | No horizontal scroll, form usable; screenshot reviewed |
| 3 | Submit a fresh email | Success panel appears; `marketing_leads` row exists with `interest='waitlist'`, `source_page='/waitlist'` |
| 4 | Confirmation email path | Backend log shows the waitlist confirmation attempt (local run has no SendGrid key, so the "NOT sent, key empty" log line IS the proof the send path fired); `confirmation_email_sent_at` set by the claim |
| 5 | Duplicate submit (same email) | Success shown, no new row, no second send log |
| 6 | Honeypot (fill `company` via JS) | Success shown, no row created |
| 7 | Backend stopped, submit | Honest error with hello@ fallback line, no crash |
| 8 | CTA sweep: `/`, `/pricing`, `/features`, `/demo`, `/agents`, `/brokers-teams` | Zero anchors to `/register` except Login; waitlist CTAs present where §5.4 says |
| 9 | `/create-account` | Waitlist card renders, "Already invited?" still reaches the app register |
| 10 | Early-access + demo-modal surfaces (`/fsbo`, demo modal) | Unchanged, still submit their own interests |
| 11 | Platform admin: login as platform admin, `/platform/waitlist` | Row from #3 visible; interest filter and search work; non-admin gets 404-style denial |
| 12 | CSV export click | File downloads (forced save, no navigation); contents match the filtered table incl. the #3 row |
| 13 | `VITE_WAITLIST_MODE=false` smoke run | Site reverts: "Create an account" CTAs back everywhere, `/waitlist` still reachable directly |

### 9.3 Stage before prod

One real signup on stage with a personal address to read the actual delivered email (SendGrid key present on stage), confirm sender shows "Velvet Elves \<hello@velvetelves.com\>", links work, both HTML and plain-text parts render.

---

## 10. Rollout, ops, and open items

Order: (1) apply migration to stage DB → (2) deploy backend → (3) deploy marketing site with `VITE_WAITLIST_MODE=true` → (4) stage E2E incl. the real email → (5) same order on prod. The marketing site deploy is safe before backend only for browsing, not for signups with the new interest (CHECK constraint would reject `waitlist`), hence backend first.

Ops notes:
- Prod CORS: `CORS_ORIGINS` env on prod must include the marketing domain (the deployment plan already calls for this; verify, since the public endpoint is browser-called cross-origin).
- SendGrid: domain auth covers hello@; verify `SENDGRID_API_KEY` is set in the prod task definition + Secrets Manager (runtime truth is the ECS task def, not `.env` files).
- The confirmation email is request-path (fires on signup), so it does NOT depend on the prod scheduler, which is still never wired. No dependency there.
- Launch day (R3's "for now"): set `VITE_WAITLIST_MODE=false`, redeploy the marketing site. Optionally then remove the nav/footer Waitlist links in the same change.

For Jake (none block implementation):
1. Copy sign-off for the confirmation email (§7) and page (§8).
2. Nav prominence: keep "Watch demo" as the top-bar gradient button (my default), or swap it for "Join the waitlist" while in waitlist mode?
3. Before any bulk mail to this list (demo blast, launch invite), we need a real unsubscribe mechanism; the one-time confirmation's reply-to-leave line is fine for now but does not scale.

Estimated scope: ~6 new files (migration, email service, platform API, platform test, WaitlistPage, PlatformWaitlistPage + hook), ~14 edited files, no changes outside the described surfaces. I implement and verify; Jan commits (no auto-commits).

---

## 11. Implementation record (2026-07-29)

Everything in §4-§6 is built. Three deviations from the plan, all deliberate:

1. **Email rendering and delivery were extracted, not duplicated.** §4.3 offered a
   choice; importing privates (`_shell`, `_p`, `_signoff`) across modules is a smell,
   so the shell/paragraph/button/sign-off helpers moved to
   `app/services/platform_email_rendering.py` and the async SendGrid transport to
   `app/services/platform_mailer.py`. `welcome_email_service` now uses both, and its
   `_deliver` survives unchanged as a thin WELCOME-purpose wrapper. Two platform
   emails can no longer drift into two slightly different brands. The three welcome
   delivery tests moved their `httpx` patch to `platform_mailer`; assertions unchanged.
2. **`marketing_site_url` setting added** (default `https://velvetelves.com`) so the
   confirmation email links to marketing pages. A waitlist signup has no account; an
   app link would be a login wall.
3. **An OG share image was generated** (`public/og/waitlist.png`), matching the house
   card design. Every indexable route has one and `Seo` derives the path by slug, so
   without it the page Jake links in ads would have shipped a 404 share image.

### Two real bugs found and fixed while verifying

- **Every email field on the site was 21px tall on mobile.** `EmailCapture`'s input
  carried `flex-1`; below `sm` the wrapper is a *column*, so `flex-basis: 0` applied
  to the HEIGHT and overrode `h-12`. Desktop was fine (48px), which is why it went
  unnoticed. Now `sm:flex-1`. This fixes the newsletter strip, demo modal, and
  early-access captures too — a thumb-sized tap target on exactly the devices ad
  traffic lands on.
- **CSV export revoked its object URL synchronously after `click()`.** The browser
  reads the blob asynchronously; revoking immediately is a documented way to lose the
  file. Deferred. NOTE: `PlatformCostsPage.tsx` and `PlatformAIUsagePage.tsx` still
  have the synchronous pattern — worth the same one-line change.

### Verification actually run

- Backend: **1376 passed**, `ruff` clean. Marketing site and app frontend builds green
  (`tsc --noEmit` + SSG prerender; `dist/waitlist.html` carries the real headline,
  sitemap grew to 17 urls).
- Real Chrome against a fresh backend + both dev servers, migration applied to the dev
  DB. All 13 plan checks pass, plus DB-state assertions.
- Confirmation email: run with `SENDGRID_API_KEY` deliberately EMPTY, so the send path
  logs instead of mailing fake addresses (bounces at `@example.com` would cost sender
  reputation). Log proves it fired **once per unique waitlist signup**, with the right
  subject, and **zero times** for duplicates, the honeypot, and every other segment.
  `confirmation_email_sent_at` stamped by the atomic claim.
- CSV: this machine's Chrome cancels *every* `blob:` download routed through CDP
  (verified with a bare 8-byte blob, headless AND headed), so the assertion checks the
  exact bytes handed to the browser instead of a file landing on disk: correct header,
  2 filtered rows, `text/csv`, filename `waitlist-2026-07-29.csv`, forced save with no
  navigation. **The file-write step itself is unverified in this environment** — worth
  one manual click on stage.
- All E2E rows, the test platform-admin account, its tenant, audit rows, and its
  communication log were deleted afterwards; `marketing_leads` is back to 0 rows.

### Still open

- §9.3 stage check (a real delivered email, read in an inbox) — needs a stage deploy.
- Jake's copy sign-off (§7, §8) and the nav-prominence question.
- Unsubscribe infrastructure before any bulk send to this list.
