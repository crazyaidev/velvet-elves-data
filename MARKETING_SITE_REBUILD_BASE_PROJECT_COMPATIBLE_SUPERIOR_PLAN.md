# Velvet Elves Marketing Site — Rebuild (Base-Project-Compatible) Superior Plan

**File:** `MARKETING_SITE_REBUILD_BASE_PROJECT_COMPATIBLE_SUPERIOR_PLAN.md`
**Author:** Jan (sole developer)
**Date:** 2026-06-26
**Status:** Plan only. **No source code is written by this document.** It defines the strategy, architecture, design system, page-by-page build, phasing, and test gates for a new marketing website built in a new folder: `Projects/velvet-elves-marketing-new`.

> **Why this plan exists, and what makes it different.** Prior plans broke down in front-end testing because they were drafted without first reconciling *all* of the project's sources of truth — product requirements, system design, the existing front-end/back-end source, **and** Jake's existing marketing site — against each other. The result was end-to-end workflows that snapped under a real tester's click path. This plan is grounded in a documented review of that whole corpus (§2), and every page and flow is specified to be **completable by a non-developer real-estate professional using the mouse, with near-zero typing** (§9, §12). The aesthetic target is a **modern, professional tool for real-estate experts that visually harmonizes with the actual product** (§6).

---

## 0. How to read this document

- §1 — Executive summary and the three locked foundations (with rationale).
- §2 — Evidence base: exactly what was reviewed, so the plan demonstrably rests on the full corpus.
- §3 — Jake's vision, distilled and preserved.
- §4 — The compatibility thesis: stack, design language, integration, deployment.
- §5 — Information architecture (sitemap, nav, footer).
- §6 — Design system: what to port from the app, and the marketing-specific extensions.
- §7 — Technical architecture (Vite + React + static prerender + SEO + lead capture + hand-off).
- §8 — Component kit and page-by-page build briefs.
- §9 — UX & workflow principles (mouse-first, minimal-typing, testable-by-realtors).
- §10 — Honesty & claims governance (no invented proof; capability truth-check).
- §11 — Phased execution plan with acceptance criteria.
- §12 — Testing & validation (non-dev UAT scripts + automated gates).
- §13 — Deployment & operations.
- §14 — Risks, open questions, decisions needed.
- §15 — Definition of done / launch checklist.
- §16 — Post-v1 backlog.

---

## 1. Executive summary

We are rebuilding the public marketing site as **`velvet-elves-marketing-new`**, a standalone web surface that **sells the same vision Jake authored** but is **built in the base project's own stack and design language** so that the journey from *marketing → sign-up → product* feels like one continuous, premium product — and so that one developer can maintain the whole estate with a single toolchain.

Three foundations are **locked** (confirmed with Jan, 2026-06-26):

1. **Stack — match the base front-end.** Vite + React 18 + TypeScript + Tailwind + Radix/shadcn primitives (the exact toolchain of `velvet-elves-frontend`), with a **build-time static prerender layer** added for SEO/AEO parity with Jake's Next.js static export. One toolchain; direct reuse of the app's tokens and primitives.
2. **Brand & design — adopt the VE app design system.** Use the base project's `ve-*` tokens, **IBM Plex Sans + Lora + IBM Plex Mono**, and `STYLE_GUIDE.md` as normative. Keep Jake's **strategy** (narrative, audiences, CTA model, "Meet the Elves", no-pricing) but render it in the product's visual language so marketing and app are visibly one brand.
3. **Integration — hand off, stay decoupled.** "Create an account" deep-links into the **real app sign-up** (`app.velvetelves.com/register`); lead capture writes to a **separate insert-only store** (never the product DB); the site **deploys independently** (its own S3/CloudFront), so the marketing site can never take down the app. This matches the AWS deployment plan, which already treats the marketing site as a *separate web surface* on `velvetelves.com`.

**The pleasant surprise that validates foundation #2.** Jake's own *Visual Direction Guide* asks for "warm neutrals… champagne… muted gold… soft teal," a "rich dark color instead of pure black," and explicitly warns **against "cold enterprise blue"** and generic SaaS blue buttons. His built marketing site nevertheless shipped a **Navy `#16243A` + Tennessee-Orange `#FF8200`** palette with **Geist/Inter**. The base project's `ve-*` system — **champagne `#E26812/#EE7623`**, warm ivory/sand surfaces, charcoal-navy `#2C4C7F`, Lora serif accents, a "calm premium concierge" voice — is **a closer match to Jake's stated visual intent than his own marketing palette was.** Adopting the app design system is therefore not a compromise of Jake's vision; it is a *more faithful execution* of his Visual Direction Guide, with the bonus of brand continuity into the product.

**The hero, reconciled (revised after source audit — see §1A/F3).** Jake "locked" a *full-bleed activity-video hero* whose signature is the **rotating tagline "Your transaction keeps moving while you're ___."** The video assets do not exist and were **parked**, but the *rotating tagline is the locked emotional core* and his built hero already runs it on gradient placeholders. His own Visual Direction Guide also calls for a **split hero with a floating transaction command-center mockup**. These are not in conflict. v1 builds a **split hero that keeps the rotating tagline H1** (left) and adds a coded command-center mockup (right) — preserving the locked emotional argument *and* the Visual Direction Guide, with no video dependency. The full sentence (default word "skydiving") still renders server-side for SEO. The full-bleed activity video is the only post-v1 enhancement.

**The honesty correction that changes v1 scope (revised after source audit — see §1A/F1).** Jake's site markets **all four Elves as live**, but the backend ships **only Inbox- and Compliance-class capability**. SMS and Voice are **Protocol-only stubs that raise `NotImplementedError`** (`app/services/communication_providers.py`), and `requirements.txt` §6.7/§12.4 list SMS & Voice as *future hooks*. Therefore v1 presents **Inbox Elf and Compliance Elf as live** and **Voice Elf and SMS Elf as "coming soon"** (or omits them) — and removes the voicemail/SMS entries from the product's `featureList`/JSON-LD. This overrides Jake's locked decision #9, with code evidence.

---

## 1A. Review log — corrections from auditing Jake's implemented source + the base project (2026-06-26)

This section records a line-by-line audit of Jake's **built** `velvet-elves-marketing` source (not just his docs) and the base front-end/back-end, run specifically to find workflow/logic flaws before any code is written. Each finding cites evidence and states the correction now folded into the plan. **F1, F3, and F4 are end-to-end workflow breaks** — exactly the class of failure this rebuild exists to prevent.

**F1 — [Honesty / workflow break] Two of the four Elves are not real.** Jake's `components/sections/MeetTheElves.tsx` presents **Voice Elf** ("Transcribes voicemails and calls") and **SMS Elf** ("Sends… text updates to clients, co-agents, and vendors") as live, and `app/page.tsx` lists "Voicemail and call transcription" + "Client, co-agent, and vendor SMS updates" in the homepage **SoftwareApplication `featureList`**. *Evidence:* `velvet-elves-backend/app/services/communication_providers.py` ships `SmsProvider`/`VoiceProvider` as **Protocol-only**; `UnconfiguredSmsProvider.send_sms` and `UnconfiguredVoiceProvider.initiate_call` **raise `NotImplementedError` ("…not yet wired up. Phase 6/7 ships the Twilio adapter")**; `get_sms_provider()`/`get_voice_provider()` are "always the unconfigured stub today." `requirements.txt` §6.7 ("SMS & Voice Communication **Hooks**") and §12.4 ("**Expanded** AI Agents (voice, SMS, calendar)") confirm these are future. *Correction:* v1 markets only **Inbox Elf** (AI email triage/draft + approval-before-send) and **Compliance Elf** (deadline/disclosure/checklist tracking + audit trail) as live; **Voice/SMS are labeled "coming soon" or omitted**; remove them from `featureList` and SoftwareApplication JSON-LD. See the capability matrix in §10.1.

**F2 — [Workflow] "Watch demo" has two behaviors; the plan and UAT assumed one.** *Evidence:* `components/nav/Nav.tsx` wires **"Watch demo" → `href="/demo"`** (a page), while `HeroSection.tsx` and `FinaleSection.tsx` open the **`DemoModal`** in place. Both are honest, but my first draft said "Watch-demo opens the modal everywhere" and the UAT asserted a modal on every click. *Correction:* in-page CTAs open the `DemoModal`; the **nav routes to `/demo`** (which itself shows the honest in-production player + capture). §3.4, §8, §9, and the §12 UAT now state both behaviors.

**F3 — [Vision fidelity] The first draft discarded Jake's locked rotating tagline.** *Evidence:* `HeroSection.tsx` is the rotating-tagline hero (`SCENES[]` cycling skydiving/hiking/…/asleep) on gradient placeholders; the rotator + sentence is locked decision #5 and is rendered server-safe with default "skydiving." *Correction:* the v1 hero keeps the rotating tagline and adds the command-center mockup in a split layout (see §1, §8 page 1).

**F4 — [Workflow break] FSBO and Attorney audiences cannot self-sign-up, but are given "Create an account" CTAs.** *Evidence:* `velvet-elves-frontend/src/utils/accountTypes.ts` `ACCOUNT_TYPES_NOW` = **Agent, Team Leader, Transaction Coordinator, Admin only**; "Attorney + FSBO follow (Phase A2), vendors in the vendor phase (A3). Client is never self-sign-up." Jake's `/fsbo` page and the Attorney audience nonetheless funnel to "Create an account." A FSBO visitor who clicks it lands on a register screen with no FSBO option — a dead end. *Correction:* per-audience CTA routing (§10.1): audiences that **can** self-register (Agents, Teams, TCs) get "Create an account" → `/register`; audiences that **cannot yet** (FSBO, Attorney, Clients) get **Watch demo + Join early access** as primary, and any account CTA routes to the early-access capture, never to a register screen that excludes them.

**F5 — [Handoff accuracy] Create-account routes to bare `APP_URL`; role-prefill is not yet supported by the app.** *Evidence:* `app/create-account/page.tsx` links `href={APP_URL}` ("Continue to the app"), not `/register`. The app *does* expose `ROUTES.REGISTER = '/register'`, but `RegisterPage.tsx` uses `defaultValues: { account_role: DEFAULT_ACCOUNT_ROLE }` and **reads no query param** — so my first-draft `/register?role=…` deep-link would silently do nothing. *Correction:* v1 links to **`${APP_URL}/register`** (a real, more useful target than bare `APP_URL`); **role-prefill via `?role=` is a coordinated follow-up that requires a small `RegisterPage` change** (read the param into `account_role`), which is *out of scope for the decoupled marketing site*. §4.3/§7.6/§14-Q3 updated.

**F6 — [Accessibility] The app's default button fails Jake's CTA-contrast rule for normal-size text.** *Evidence:* `velvet-elves-frontend/src/components/ui/button.tsx` default = `bg-primary text-primary-foreground`; `index.css` sets `--primary: 24 85% 48%` (≈ `#E2680F`) and `--primary-foreground: 0 0% 100%` (white). White-on-`#E2680F` ≈ **3.3:1 — fails WCAG AA for normal text** (passes AA-large ≥3:1 only for ≥24px or ≥18.66px-bold). Jake's hard rule: "never white-on-orange." *Correction:* marketing primary CTAs either keep **large/bold** text (AA-large) **or** use **`ve-orange-dark` `#C05A0A`** as the button background (white text ≈ 4.6:1, AA at all sizes) **or** champagne bg with **charcoal/`ve-orange-xdark` text**. A `MarketingCTA` wrapper standardizes this. §6.2/§6.3 updated.

**F7 — [Robustness, low] The DemoModal is a hand-rolled overlay with the known backdrop-close pattern.** *Evidence:* `DemoModal.tsx` closes on `e.target === overlayRef.current` (click target only, no pointerdown-origin guard) — the latent text-selection-drag close bug. *Correction:* in the rebuild the modal uses the app's **Radix `Dialog`** (immune by construction); reaffirmed in §6.3/§7.5.

**F8 — [SEO porting gap] Jake's SEO leans on Next-only primitives the Vite build lacks.** *Evidence:* `app/opengraph-image.tsx` uses `next/og`; `app/sitemap.ts`/`robots.ts` use Next route conventions; JSON-LD is injected via server-component `<script type="application/ld+json">`. PROGRESS.md notes `force-static` gotchas. *Correction:* §7.4 now specifies the Vite equivalents — JSON-LD serialized into the prerendered HTML; OG image as a **static asset or a `satori`/`@vercel/og` build step** (no `next/og`); `sitemap.xml` + `robots.txt` produced by a **build script** that enumerates the route table.

**F9 — [Copy/UX, low] One EmailCapture button label for three contexts; "Subscribe" is wrong for a demo waitlist.** *Evidence:* `EmailCapture.tsx` always renders "Subscribe"/"Subscribing…", even for `interest='demo_waitlist'`/`'early_access'`. *Correction:* the rebuilt `EmailCapture` adapts its label to `interest` ("Notify me" / "Request invite" / "Subscribe"). §7.5.

**F10 — [Test rigor, low] `verify-rls.mjs` counts an empty SELECT as "blocked."** *Evidence:* it passes SELECT when `selectErr || !rows?.length`; an empty table would also pass. *Correction:* keep the row-count check but **seed one row via the privileged path first** (or assert the explicit policy denial) so "0 rows to anon" proves RLS, not emptiness. §12.2.

**F11 — [Confirmed-good, keep] Patterns Jake got right that the rebuild preserves.** The float→lock→transparent nav math (`Nav.tsx`), `prefers-reduced-motion` gating on the rotator/finale magnetic button, the self-assembling How-it-works mockup with the visible "Prototype screen" caption, the honest "Demo in production" modal, the insert-only `marketing_leads` shape, and the single-source `faqPageJsonLd(faqs)` feeding both the visible accordion and the structured data. These carry over (re-skinned to `ve-*`).

**F12 — [Token-map, do this in Phase 0] The two repos use different token *names*; mockups must be re-pointed.** Jake's `HowItWorks` mockup uses his marketing `ve-*` *product* tokens (`ve-bg #FAF8F5`, `ve-ink #2C2416`, `ve-success #3A6B4E`, etc.), which are **different values and names** from the base app's `ve-*` system. *Correction:* the rebuild's mockups use the **base app's** `ve-*` tokens (copied verbatim per §4.2); do not copy Jake's mockup hex. Status pills inside mockups use the app's `ve-green/amber/red/blue` triads.

---

## 2. Evidence base (what was reviewed before drafting)

This plan was written only after reviewing the following. It is listed so the foundation is auditable.

**Jake's existing marketing site (`velvet-elves-marketing/`)** — the source of his vision:
- `CLAUDE.md` / `AGENTS.md` (standing law: locked decisions 1–12, copy rules, engineering rules, workflow).
- `BUILD-PLAYBOOK.md` (his 0–11 phase model and per-phase acceptance gates).
- `PROGRESS.md` (what actually shipped: Phases 0–10; Phase 5 video parked; 13 pages live).
- `docs/01-master-strategy.md`, `docs/02-sitemap-and-seo.md`, `docs/03-design-tokens.md`, `docs/04-supabase-spec.md`.
- `docs/source-copy/` — including **Velvet Elves Marketing Site Visual Direction Guide**, **Homepage** (CTA system), Site Schema, Navigation Structure, Trust and Proof Strategy, AEO & SEO Strategy, For Agents, FSBO, Consumer Portal, Brokers & Teams, plus the post-v1 role docs (Attorneys, TC, Vendor).
- **Built code, read in full this pass (not just docs):** `tailwind.config.ts`, `next.config.ts`, `app/layout.tsx`, `app/page.tsx`, `app/create-account/page.tsx`, `app/demo/page.tsx`; `components/hero/{HeroSection,DemoModal}.tsx`, `components/nav/Nav.tsx`, `components/sections/{MeetTheElves,HowItWorks,TrustBand,StatementStrip,FinaleSection}.tsx`, `components/ui/{Button,EmailCapture}.tsx`, `components/footer/{Footer,EmailCaptureStrip}.tsx`; `lib/{config,seo,supabase,utils}.ts`; `scripts/verify-rls.mjs`. These are the basis for findings §1A/F1–F12.

**Base project — product truth and the target design language:**
- `velvet-elves-frontend`: `package.json` (Vite 6, React 18, React Router 7, Tailwind 3.4, Radix, TanStack Query, framer-motion, lucide-react, react-hook-form, zod), `tailwind.config.js` (the `ve-*` token source), `src/index.css` (CSS variables, font stack), `index.html` (font loading).
- In-repo marketing-grade reference: `src/pages/public/AdvertiseLandingPage.tsx` + `AdvertiseShell.tsx` — a polished public landing built *inside* the VE design system with restrained framer-motion (`MotionConfig`, `useReducedMotion`, blur-up reveals). **This is the closest existing pattern; emulate its motion grammar.**
- Sign-up hand-off target: `src/pages/auth/RegisterPage.tsx` (role at sign-up via `ACCOUNT_TYPES_NOW`, OAuth/Google, password policy; **reads no `?role` param**), `src/utils/accountTypes.ts` (`ACCOUNT_TYPES_NOW` = Agent/TeamLead/TC/Admin), `src/utils/constants.ts` (`ROUTES.REGISTER`), `src/components/ui/button.tsx` + `index.css` `--primary*` (the CTA-contrast finding, §1A/F6), `AuthLayout.tsx`, `auth/*`.
- **Back-end capability ground truth:** `velvet-elves-backend/app/services/communication_providers.py` (SMS/Voice = Protocol-only stubs raising `NotImplementedError`; the basis for §1A/F1).
- `velvet-elves-data/STYLE_GUIDE.md` — **normative** UI/UX law (brand voice, color, type, spacing, components, anti-patterns).
- `velvet-elves-data/requirements.txt` — real RBAC roles & capabilities (Agent, Elf/TC, Team Lead, Attorney, Administrator, Client, FSBO) and the AI-communication-approval model.
- `velvet-elves-data/SYSTEM_DESIGN.md` — audit trail, role-based access, transaction/document model (grounds the honesty rules in §10).
- `velvet-elves-data/AWS_ECS_CLOUDFRONT_PRODUCTION_DEPLOYMENT_PLAN.md` — domain model (`velvetelves.com` marketing, `app.velvetelves.com` app, staging mirrors), and the explicit statement that the marketing site is a *separate web surface deployed outside the app cutover*.

**Memory (Jan's standing preferences)** that constrains this plan: *I-not-we / no em-dashes* in prose; *list surfaces = table+modal+modern selectors*; *no demo/sample data on real surfaces — honest empty states*; *flat modern "specialized tool" aesthetic*; *verify rendered output, not just the mechanism*; *render + screenshot before declaring done*; *autonomous execution in order, no commits (Jan commits)*.

---

## 3. Jake's vision, distilled and preserved

The rebuild keeps **all of the strategy** below. Only the *visual execution* and the *stack* change.

### 3.1 The product story
Velvet Elves is an **AI-first "Transaction OS" for real estate**. The brand idea: a team of tireless, invisible "elves" runs the busywork between contract and closing, and **nothing moves without the user's approval**. The core emotion is **"Everything is handled."** The site is the calm opposite of transaction chaos.

### 3.2 Voice (locked)
Calm, confidence-building, concierge. Bold visuals + composed words. Never hype, never exclamation marks, no jargon, no "AI discovered electricity" energy. Address the user in second person. This is *identical* to `STYLE_GUIDE.md §1` ("calm, premium, AI-assisted… like a high-end concierge, not a SaaS dashboard") — so the app's voice rules carry straight over.

### 3.3 Audiences (v1 priority order)
1. **Agents** — want time back and a five-star client experience without hiring a TC.
2. **FSBO sellers** — professional transaction safety without an agent.
3. **Clients (buyers/sellers via portal)** — clarity on what's happening and what's next.
4. **Brokers & Teams** — pipeline visibility without micromanaging (nav present; full page post-v1).
Post-v1: **Attorneys, TCs, Vendors** (source copy already exists for all). These map cleanly to the real RBAC roles in `requirements.txt`.

### 3.4 Conversion model (locked; behavior clarified per §1A/F2)
- **Primary CTA sitewide: "Watch demo."** The demo film does not exist yet. **In-page** Watch-demo buttons (hero, finale, role finales) open an honest **"demo in production" modal with early-access email capture**; the **nav** Watch-demo routes to **`/demo`**, which shows the same honest in-production player + capture. Never embed a fake video. (This mirrors Jake's built behavior.)
- **Secondary CTA: "Create an account"** → the real app sign-up at `${APP_URL}/register` **— but only for audiences that can self-register today** (Agents, Teams, TCs). For FSBO/Attorney/Client audiences (not yet self-sign-up, per §1A/F4) the primary path is **Watch demo + Join early access**.
- **Soft CTA:** Join early access / get updates (email capture).
- **No pricing anywhere on v1.** No ListedKit comparison on v1 (proof first).

### 3.5 Homepage narrative arc (preserved; hero medium reinterpreted per §1)
Hero → Statement ("every deal generates a hundred small jobs; right now you do all of them") → **Meet the Elves** (Inbox, Voice, SMS, Compliance) → How it works (forward what you have → elves organize → you approve, they execute; a self-assembling dashboard mockup) → Role cards → **Trust band** (audit trail, role-based access, you approve everything) → Finale CTA.

### 3.6 Trust & proof rules (locked — see §10)
- **Never invent** testimonials, statistics, client counts, awards, or quotes.
- Product visuals are **coded UI mockups in the product's own design language**, always honestly labeled ("Prototype screen").
- **Only claim live capabilities.** Roadmap items are labeled "coming soon" or omitted.

### 3.7 SEO/AEO intent (locked — see §7.4)
Static HTML for every page; full H1 server-rendered; answer-engine "What is…" blocks atop role/guide pages; JSON-LD (Organization, WebSite, SoftwareApplication, FAQPage, HowTo, BreadcrumbList); `sitemap.xml` + `robots.txt`; unique per-page title/description/canonical/OG.

---

## 4. The compatibility thesis (stack · design · integration · deployment)

### 4.1 Stack: Vite + React + a static prerender layer
We mirror `velvet-elves-frontend` so primitives and tokens are shared, then close the only gap (a pure SPA is poor for SEO) with **build-time static prerendering**.

- **Primary recommendation: `vite-react-ssg`.** It renders every route to complete static HTML at build time and hydrates on the client, and integrates head/meta management. This gives us Jake's "every page ships complete HTML / H1 server-rendered / JSON-LD in source" guarantees *without leaving Vite/React*. Output is a static `dist/` deployable to S3/CloudFront exactly like the app frontend.
- **Alternative:** React Router 7 "framework mode" with `prerender` (the app already uses `react-router-dom@7`). Heavier migration; keep as fallback only.
- **Rejected:** a plain client-rendered SPA (fails the SEO/AEO mandate Jake invested in).

Shared dependencies copied from the app at matching majors: `tailwindcss@3.4`, `framer-motion@12`, `lucide-react`, `clsx`, `tailwind-merge`, `react-hook-form` + `zod` (for the email-capture field only). No TanStack Query, no react-router app shell, no auth context — the marketing site is content + one tiny insert.

### 4.2 Design language: adopt the app's system verbatim, extend for marketing scale
- **Port the token source verbatim.** Copy `ve-*` colors, `fontFamily`, `fontSize`, `borderRadius`, `boxShadow`, and keyframes from the app's `tailwind.config.js`, and the `:root` CSS variables + `.font-serif/.font-mono` utilities from `src/index.css`. **Single source of truth; never hand-retype hex.** (Note the app's two near-identical orange values — `ve.orange.DEFAULT #E26812` in Tailwind vs `--ve-orange #EE7623` in CSS — both are the champagne family; copy both files as-is and do not "fix" them.)
- **Typography:** IBM Plex Sans (body/UI), **Lora** (serif headlines/"protagonist" titles), IBM Plex Mono (small-caps "kickers"). Self-host via `@fontsource/*` packages (not the app's Google-Fonts `<link>`) so the marketing site meets Jake's "no render-blocking font CDN" performance rule while staying in Vite.
- **Marketing-scale extensions (additive, not contradictory).** Jake's Visual Direction Guide wants a *bigger, more editorial* scale than the dense product UI. Add marketing-only display sizes (hero `clamp(40px→72px)`, section `clamp(28px→48px)`) as **component-level classes** in the marketing repo — never edit the ported product tokens. The product's `STYLE_GUIDE` density rules govern the **mockups**; the marketing display scale governs the **page chrome**. Both draw from the same families and palette, so they read as one brand at two zoom levels.
- **One palette, two contexts, cleanly separated** (this resolves the old site's split): in Jake's site, "site chrome" used Navy/Tennessee-orange while "product mockups" used a *different* product palette. Here, **chrome and mockups share the single `ve-*` system**, because `ve-*` *is* the product identity. Simpler, and strictly more coherent.
- **Champagne discipline = the union of both rule sets.** Jake's "orange ≤ ~5% per screen, navy/charcoal text on orange, spice not sauce" and `STYLE_GUIDE`'s "champagne reserved for AI/brand/primary-CTA moments, never decoration" say the same thing. Enforce the stricter reading. (Where Jake's rule said "navy text on orange," our CTA equivalent is the app's `bg-ve-orange` button with its established foreground; verify AA at build.)
- **Motion grammar:** restrained, calm, `ease-out`, **no bounce/spring overshoot** (Jake and `STYLE_GUIDE §8` agree). Reuse the reveal language from `AdvertiseLandingPage.tsx` (blur-up `y:34→0`, `EASE_OUT [0.16,1,0.3,1]`, `whileInView once`, `MotionConfig` + `useReducedMotion`). Every animation has a reduced-motion path.

### 4.3 Integration: decoupled hand-off
- **Config constant, never inline.** `lib/config.ts` exports `APP_URL` (default `https://app.velvetelves.com`, env-overridable to `app.stage.velvetelves.com`). Every "Create an account" / "Sign in" routes through it.
- **Hand-off target (corrected per §1A/F5).** "Create an account" → **`${APP_URL}/register`** (the app exposes `ROUTES.REGISTER = '/register'`). **Do not append `?role=` in v1:** `RegisterPage` reads no query param today (`defaultValues: { account_role: DEFAULT_ACCOUNT_ROLE }`), so a role param would silently do nothing. Role-prefill is a *coordinated follow-up* requiring a small app-side change (read `?role` into `account_role`), tracked in §14-Q3 and out of scope for the decoupled marketing build.
- **Audience-aware routing (corrected per §1A/F4).** Only **Agent / Team Leader / Transaction Coordinator** are in the app's `ACCOUNT_TYPES_NOW`. **FSBO, Attorney, and Client are not self-sign-up yet**, so their pages must NOT funnel to `/register` (dead end). Their account CTA routes to the **early-access EmailCapture** until the app adds those roles (Phase A2/A3).
- **Lead capture stays out of the product DB.** A single insert-only `marketing_leads` table in a **marketing-dedicated Supabase project** (mirroring Jake's decoupling, project `mooktjgryaozlbaxgmei`), `anon` may INSERT only — verified SELECT/UPDATE/DELETE all fail before any form is wired. One shared `<EmailCapture>` (interest + source_page + honeypot + disable-on-submit + honest success/failure). No other data is ever collected.
- **No shared runtime, no shared auth session.** The marketing site never imports the app's auth context or calls the product API. The only network write is the lead insert.

### 4.4 Deployment: independent static surface
Per the AWS plan's domain model: marketing = `velvetelves.com` (prod) / `stage.velvetelves.com` (staging); app = `app.velvetelves.com`. Build `dist/` → its **own S3 bucket + CloudFront distribution**, separate from the app's. DNS in GoDaddy for now (Route 53 later). Marketing deploys on its own cadence and cannot affect the app. (Details in §13.)

---

## 5. Information architecture

### 5.1 v1 page inventory (keep Jake's 13; same routes)
| # | Route | Page | Primary job |
|---|---|---|---|
| 1 | `/` | Homepage | Belief: "everything is handled." |
| 2 | `/demo` | Watch Demo | Honest "in production" + email capture. |
| 3 | `/create-account` | Account router | Thin page → `APP_URL/register` (noindex). |
| 4 | `/product` | Product Overview | The four Elves as live capabilities. |
| 5 | `/how-it-works` | How It Works | Forward → organize → approve → execute. |
| 6 | `/agents` | For Agents | Conversion page for agents. |
| 7 | `/client-portal` | Client Portal | The buyer/seller experience. |
| 8 | `/fsbo` | FSBO | Conversion page for FSBO sellers. |
| 9 | `/faq` | FAQ | Grouped, quotable answers (FAQPage). |
| 10 | `/guides/contract-to-close` | Guide | Educational HowTo + Breadcrumb. |
| 11 | `/about` | About | Facts-only narrative (no invented history). |
| 12 | `/contact` | Contact | Card + reused EmailCapture. |
| 13 | `/legal` | Privacy & Terms | Plain-language scaffolds (attorney review pre-launch). |

Reserve nav structure for post-v1: `/brokers-teams`, `/attorneys`, `/transaction-coordinators`, `/vendors`, `/blog`, `/compare/listedkit`, remaining guides. (No orphan links; placeholders resolve to real anchors until pages exist, e.g. Brokers → `/agents#teams`, Attorneys → `/faq#attorneys`.)

### 5.2 Navigation (reinterpreted in the VE design language)
A **floating pill nav** (Jake's signature) rebuilt with `ve-*` tokens: detached rounded bar near the top; on scroll it locks flush with a frosted `bg-white/85 backdrop-blur` + `border-ve-border` hairline; transparent variant over the hero. Contents: wordmark · role menu (For Agents · Brokers & Teams · FSBO · Attorneys) · "Sign in" (ghost link → `APP_URL`) · **"Watch demo"** (`bg-ve-orange` primary). Mobile: wordmark + Watch demo + hamburger sheet (use the app's Radix Dialog/sheet pattern). Keyboard-navigable; AA contrast; ≥44px touch targets.

### 5.3 Footer
Four columns — **Product** (Product, How it works, Demo) · **Who it's for** (Agents, FSBO, Client Portal) · **Learn** (Guide, FAQ) · **Company** (About, Contact, Legal) — with the email-capture strip above it. Every page reachable within 2 clicks of home.

---

## 6. Design system specification

> Governing rule: **when in doubt, copy an existing app pattern that already conforms** (`STYLE_GUIDE §17`). The marketing site introduces *no new color, shadow, or dialog shape* — it composes the app's vocabulary at a larger editorial scale.

### 6.1 Color & the chrome/mockup split
- **Surfaces:** warm light canvas alternating `ve-bg`/`#FAFAF8` (warm) ↔ `ve-surface` white; dark "drama" sections (trust band) use `ve-sidebar #1E3356` / charcoal-navy gradients — this is Jake's "rich dark instead of pure black" and the app's sidebar navy in one move.
- **Accent:** champagne `ve-orange*` only on primary CTAs, the brand "✦" kicker, small badges, focus rings, and one-per-section glow. ≤5% per viewport; if orange appears in >3 distinct elements on a screen, remove the least important.
- **Status triads** (`ve-green/amber/red/blue` bg+border+text) appear **only inside product mockups** (on-track/attention/at-risk pills) — never as site-chrome decoration. Never a status color in isolation.

### 6.2 Type system
- Hero: `font-serif` (Lora) `clamp(40px→72px)` `leading-[1.05] tracking-[-0.01em]`.
- Section H2: `font-serif clamp(28px→48px)`.
- Eyebrow/kicker: `font-mono text-[12px] tracking-[1.5px] uppercase text-ve-orange` (honor `STYLE_GUIDE` v2 "no text below 12px").
- Body: IBM Plex Sans 16–18px on marketing pages (editorial scale), 13.5px inside mockups (product scale).
- One serif title per card; sentence case everywhere except mono kickers; never `font-bold` on body (use `font-semibold`).

### 6.3 Component kit (marketing — built on app primitives)
Reusable, all reduced-motion-safe, all mobile-first (verified at 375px before desktop):
- `MarketingShell` (nav + footer + `MotionConfig`).
- `Button` (port the app's `variant`/`size` API) **+ a `MarketingCTA` wrapper that fixes the contrast gap (§1A/F6).** The app's default button is white-on-`#E2680F` (≈3.3:1 — AA-large only). Marketing primary CTAs must meet AA at their rendered size: use **`bg-ve-orange-dark` `#C05A0A` + white text** (≈4.6:1) for standard-size CTAs, or champagne bg + **charcoal/`ve-orange-xdark` text**, or keep the text **large/bold** (AA-large). Never small white-on-champagne.
- `SectionShell` (reveal-on-scroll wrapper; blur-up; staggers children).
- `Eyebrow`, `RoleCard`, `StatusPill` (uses `ve-*` status triads), `AnswerBlock` (the "What is…" AEO block).
- `EmailCapture` (the only data write; §7.5).
- `DemoModal` (honest "in production" + EmailCapture; `sourcePage` prop).
- **Product mockups** as coded components in the app's design language (`InboxElfMock`, `VoiceElfMock`, `SmsElfMock`, `ComplianceElfMock`, `AgentDashboardMock`, `ClientPortalMock`, `FsboDashboardMock`, `TransactionCommandCenterMock` for the hero). Every mockup carries a visible **"Prototype screen"** caption. Reuse real component silhouettes from the app (KPI strip, milestone timeline, status pills) so screenshots feel native — these are *recreations in marketing copy*, not live app embeds.

### 6.4 Anti-patterns to avoid (from `STYLE_GUIDE §13` + Jake's Visual Direction Guide)
No card-grid graveyards (lead with emotional clarity, not feature matrices); no cold enterprise-blue chrome; no neon/AI-sparkle overload (one ✦ is plenty); no cartoon elves / North-Pole literalism; no stock "family pointing at laptop"; no `shadow-2xl`/bouncy motion; no Tailwind default colors; no white-on-orange; no native `<select>` (use the app's Radix `Select` if any picker appears).

---

## 7. Technical architecture

### 7.1 Project shape (`Projects/velvet-elves-marketing-new`)
```
velvet-elves-marketing-new/
  index.html
  vite.config.ts            # vite + react + vite-react-ssg
  tailwind.config.ts        # ve-* tokens copied from app + marketing display scale
  postcss.config.js
  tsconfig*.json
  .env.example              # VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_APP_URL
  src/
    main.tsx                # vite-react-ssg entry (routes export)
    routes.tsx              # the 13 routes
    index.css               # ported :root ve-* vars + font utilities
    lib/{config,seo,supabase,utils}.ts
    components/{nav,footer,ui,sections,role,product,demo}/...
    pages/...               # one file per route
  public/                   # og images, icons, favicons, robots is generated
  scripts/verify-rls.mjs    # proves anon insert-only before any form ships
```

### 7.2 Routing & prerender
Routes declared once and consumed by `vite-react-ssg` to emit static HTML per path. `/create-account` is `noindex`. Build produces `dist/` with one HTML file per route, each containing its server-rendered H1, meta, and JSON-LD.

### 7.3 Fonts & performance
Self-host IBM Plex Sans / Lora / IBM Plex Mono via `@fontsource`. Budgets (Jake's): Lighthouse mobile Performance ≥90, SEO=100, Accessibility ≥95; hero media lazy-loads after LCP; CLS≈0. No render-blocking font requests.

### 7.4 SEO / AEO
- Per-page `pageMetadata(...)` helper in `lib/seo.ts`: unique title ≤60, description ≤155, canonical on `velvetelves.com`, OpenGraph + Twitter, branded OG image.
- JSON-LD helpers: `organizationJsonLd`, `websiteJsonLd`, `softwareApplicationJsonLd`, `faqPageJsonLd`, `howToJsonLd`, `breadcrumbListJsonLd` — injected into static head so they appear in view-source.
- Answer blocks (2–3 sentence "What is…") atop `/agents`, `/client-portal`, `/fsbo`, `/product`, `/how-it-works`, `/guides/contract-to-close`.
- Generated `sitemap.xml` (12 indexable routes; exclude `/create-account`) + `robots.txt`.
- **Homepage title recovers the keyword the tagline lacks:** "Velvet Elves — AI Real Estate Transaction Management"; first H2 and meta description include "real estate transaction."
- **Next→Vite porting (per §1A/F8):** Jake's SEO uses Next-only primitives we do not have. Replace them: (a) **JSON-LD** is serialized into each prerendered page's HTML (render the `<script type="application/ld+json">` in the component and confirm it appears in view-source of the built file); (b) the **OG image** is a **static pre-rendered asset** in `public/`, or generated by a one-off `satori`/`@vercel/og` build script — *not* `next/og`; (c) **`sitemap.xml` + `robots.txt`** are emitted by a small build script that enumerates the route table, not by Next route files. Verify every built `dist/*.html` contains its H1 + metadata + JSON-LD.

### 7.5 Lead capture (the only write)
`marketing_leads(id, email, source_page, interest, user_agent, created_at)` in the marketing Supabase project; RLS **anon INSERT only**. `<EmailCapture interest sourcePage>` does a client-side insert with the publishable anon key from `.env.local`; honeypot + disable-on-submit; honest success ("You're on the list.") / failure ("Something hiccuped — try again."). **Submit-button label adapts to `interest`** (Notify me / Request invite / Subscribe) — §1A/F9. `scripts/verify-rls.mjs` must prove INSERT works and SELECT/UPDATE/DELETE fail **before** the component is wired; **seed one row via the service role first** so the SELECT denial proves RLS, not an empty table (§1A/F10). Auto-promote to a full review if anything about this changes.

### 7.6 The app hand-off
`APP_URL` from config; "Create an account" → `${APP_URL}/register` (no `?role=` in v1 — §1A/F5); "Sign in" → `${APP_URL}`. Audiences that cannot self-register route to early-access capture instead (§1A/F4). No other coupling.

---

## 8. Page-by-page build briefs

Each page: server-rendered metadata + JSON-LD where specified; reduced-motion safe; 375px-first; honest claims (§10); CTAs per the conversion model.

1. **Homepage `/`** — *Hero* (split, per §1A/F3: left = the **locked rotating-tagline H1** "Your transaction keeps moving while you're **[skydiving]**." — full sentence with default word server-rendered, rotator is reduced-motion-gated client enhancement — + approved sub-line "More control for agents. More clarity for clients. A calmer path to closing." + Watch demo *(opens modal)* / Create an account; right = `TransactionCommandCenterMock` rising in with a "Velvet suggests…" insight card, labeled "Prototype screen") → *Statement strip* → *Meet the Elves* (**Inbox + Compliance presented as live; Voice + SMS labeled "Coming soon" or omitted** — §1A/F1) → *How it works* (self-assembling dashboard mockup, tasks check off on scroll) → *Role cards* → *Trust band* (navy: audit trail · role-based access · you approve everything) → *Finale* (Watch demo *(modal)* + Create an account). JSON-LD: Organization + WebSite + SoftwareApplication (**`featureList` = Inbox triage + deadline/compliance tracking only; no voicemail/SMS claims**).
2. **`/demo`** — **this is the destination of the nav "Watch demo" link** (§1A/F2). Navy hero; swap-ready `DemoPlayer` (one `videoSrc` prop flips placeholder→real later); honest "in production" copy; EmailCapture(`demo_waitlist`) + Create an account; 3-step summary; role cards. Indexable.
3. **`/create-account`** — centered card → **`APP_URL/register`** ("Continue to the app", new tab); `noindex`; fallback EmailCapture(`early_access`). No fake sign-up form. Note (§1A/F4): role pages for non-self-sign-up audiences (FSBO/Attorney) should lead with early-access, not link here.
4. **`/product`** — RoleHero → AnswerBlock → **two live Elf bands (Inbox, Compliance) each with a labeled mockup, then a "Coming soon" band for Voice + SMS** (§1A/F1) → control & approvals → trust band → finale. JSON-LD: SoftwareApplication (**featureList = Inbox triage + deadline/compliance tracking only**; per §10.1).
5. **`/how-it-works`** — AnswerBlock → 3 steps (forward → organize → approve/execute) each with a mockup → lifecycle timeline (contract→close, "order varies" caveat) → who-it's-for → finale. JSON-LD: HowTo.
6. **`/agents`** — RoleHero + AnswerBlock + value sections (from `For Agents Page.md`) + labeled mockups + FAQ accordion (FAQPage) + `#teams` placeholder section + finale.
7. **`/client-portal`** — the buyer/seller clarity story (from `Consumer Portal Page.md`); **omit the two placeholder quotes** (no invented testimonials); FAQPage; finale.
8. **`/fsbo`** — FSBO safety story (from `FSBO Page.md`); FAQPage; finale.
9. **`/faq`** — grouped accordions (general/agents/fsbo/teams/portal/demo/transaction/attorneys) with `#attorneys` anchor; FAQPage JSON-LD over all Q&As; EmailCapture(`newsletter`). Omit any pricing/scheduled-live-demo Qs that conflict with locked decisions.
10. **`/guides/contract-to-close`** — guide template: breadcrumb, AnswerBlock, lifecycle overview, 11 stages (verbatim-meaning from source), orange-tint "where the elves help" callouts, guide FAQ, related links, finale. JSON-LD: HowTo + BreadcrumbList.
11. **`/about`** — facts-only narrative (Jake Stiles, broker-owner; built inside a working brokerage; the four elves; approval-first philosophy). **No invented team/funding/history.** DRAFT marker; pending Jake.
12. **`/contact`** — contact card (placeholder email until Jake confirms) + reused EmailCapture + self-serve role links.
13. **`/legal`** — plain-language Privacy + Terms scaffolds, `#privacy`/`#terms` anchors, accurate data-practice statement (email + source_page + interest + user_agent → marketing Supabase, insert-only; no ad trackers). DRAFT; attorney review before launch.

---

## 9. UX & workflow principles (the part that broke before)

These are non-negotiable acceptance criteria, not aspirations. They exist because the testers are **real-estate professionals, not developers**, and prior builds broke their click path.

1. **Mouse-first, near-zero typing.** The *only* keyboard input anywhere on the site is an email address in `EmailCapture`. Every other action is a click/tap. No multi-field forms, no sign-up form on the marketing site (sign-up lives in the app).
2. **Every CTA resolves to a real, non-dead-end destination.** No dead hrefs; nav placeholders resolve to real anchors; in-page "Watch demo" opens the modal and the nav "Watch demo" routes to `/demo` (§1A/F2); "Create an account" lands on the actual app `RegisterPage` **for self-sign-up roles only** — FSBO/Attorney/Client CTAs route to early-access capture, never to a register screen that excludes them (§1A/F4). Re-verified by the click-path UAT (§12.1).
3. **One decisive action per surface.** No more than two primary CTAs in view (Jake's rule). The whole funnel is: *see belief → Watch demo (or pick your role) → Create an account.*
4. **Honest empty/coming-soon states.** The demo is openly "in production"; roadmap capabilities are labeled or omitted (§10). No sample/demo data dressed as real proof.
5. **Accessibility = WCAG AA.** Navy/charcoal text on orange (never white-on-orange); visible focus rings (champagne); ≥44px touch targets; reduced-motion paths; every icon-only control has `aria-label`; tab order follows visual order.
6. **Mobile is the default.** Build and verify at 375px first; no horizontal overflow on any page.
7. **Continuity into the product.** Because the chrome uses the app's tokens/fonts, the moment a tester clicks "Create an account" and lands on `RegisterPage`, **nothing jars** — same serif, same champagne, same calm. That seam is the whole point of "compatible with the base project."

---

## 10. Honesty & claims governance

Grounded in Jake's Trust & Proof rules and the real product in `requirements.txt`/`SYSTEM_DESIGN.md`.

- **Capability truth-check (gate before any claim ships).** For each marketed "Elf," map the marketing claim to a **shipped** capability and cite where it lives:
  - *Inbox Elf / Compliance Elf* — AI email drafting + **human-approval-before-send** and the **audit trail / role-based access** are first-class in `requirements.txt` (AI-communication approval) and `SYSTEM_DESIGN.md` (audit_logs, RBAC). Safe to present as live, framed around *approval-first*.
  - *Voice Elf / SMS Elf* — **RESOLVED (§1A/F1): not shipped.** `communication_providers.py` ships Protocol-only stubs that raise `NotImplementedError`; `requirements.txt` §6.7/§12.4 mark SMS & Voice as future. **v1 must present these as "Coming soon" or omit them, and must not list voicemail/SMS in any `featureList`/JSON-LD.** Revisit only when the Twilio adapter (Phase 6/7) actually lands.
- **No invented proof, ever** — testimonials, stats, client counts, awards, quotes. Omit placeholder quotes from source docs.
- **Mockups are honestly labeled** "Prototype screen" and are coded recreations, not live app captures.
- **About/Legal stay factual** — no fabricated history, funding, team, or legal language that hasn't had attorney review.

### 10.1 Audience × capability × sign-up reality matrix (the end-to-end logic check)

This single table is the antidote to the workflow breaks in §1A (F1, F4). Every page's CTA and claim must agree with its row. Built from `requirements.txt` (roles/capabilities), `communication_providers.py` (SMS/voice status), and `accountTypes.ts` (`ACCOUNT_TYPES_NOW`).

| Audience | Real capability today | Can self-sign-up now? | v1 primary CTA | Marketed Elves |
| --- | --- | --- | --- | --- |
| **Agents** | Transactions, tasks, AI email (approval-first), docs, audit | **Yes** (`Agent`) | Watch demo → **Create an account** | Inbox, Compliance (live) |
| **Brokers & Teams** | Team templates, oversight, all agent caps | **Yes** (`TeamLead`) | Watch demo → **Create an account** | Inbox, Compliance (live) |
| **TCs (Elf role)** | Manage assigned transactions/tasks/docs | **Yes** (`TransactionCoordinator`) | Watch demo → **Create an account** | Inbox, Compliance (live) |
| **FSBO sellers** | FSBO workspace exists in-app | **No** (Phase A2) | **Watch demo + Join early access** (no `/register`) | Inbox, Compliance (live) |
| **Clients (portal)** | Client portal (view/ask/upload) | **No** (never self-sign-up; invited) | **Watch demo + Join early access** | n/a (it's an experience, not Elves) |
| **Attorneys** | Attorney workspace exists in-app | **No** (Phase A2) | **Watch demo + Join early access** | Inbox, Compliance (live) |

**SMS Elf and Voice Elf are "Coming soon" for every audience** until the Twilio/voice adapter ships. No page may claim them live.

---

## 11. Phased execution plan

Adopt Jake's discipline (one phase at a time; a phase is "done" only when it builds clean, passes its gate, and — for me — is left ready for Jan to commit). **No commits/branches by me** (Jan commits). Each phase lists Goal · Deliverables · Acceptance gate.

**Phase 0 — Scaffold & token port.**
Goal: empty site builds as static export with the app's design system installed.
Deliverables: Vite + React + TS + `vite-react-ssg`; `tailwind.config.ts` + `index.css` ported from the app; `@fontsource` fonts; `lib/config.ts` (`APP_URL`); `.env.example`; a placeholder home proving tokens+fonts render; `npm run build` emits static HTML.
Gate: build passes; placeholder shows Lora/Plex/champagne correctly; one route prerendered to real HTML.

**Phase 1 — Layout shell & component kit.**
Goal: floating pill nav (float→lock→transparent-over-hero), footer, and the core primitives (`Button` + the `MarketingCTA` contrast wrapper of §1A/F6, `SectionShell`, `Eyebrow`, `RoleCard`, `StatusPill`, `AnswerBlock`, `MarketingShell`).
Gate: champagne-discipline audit on nav; **every CTA passes AA at its rendered size (no small white-on-champagne — §1A/F6)**; keyboard-navigable; mobile sheet at 375px (Radix sheet); reduced-motion verified.

**Phase 2 — Lead capture (decoupled Supabase).**
Goal: `marketing_leads` table (insert-only) + `<EmailCapture>` + `verify-rls.mjs`.
Gate: the reviewer checklist — table exists with RLS on; anon INSERT works, SELECT/UPDATE/DELETE fail; nothing else touched; keys only in `.env.local` (gitignored). *(This phase touches data → highest scrutiny.)*

**Phase 3 — Homepage hero (split: rotating tagline + command-center mockup) + DemoModal.**
Goal: split hero — left = the locked **rotating-tagline H1** (full sentence + default "skydiving" server-rendered, rotator reduced-motion-gated), right = `TransactionCommandCenterMock` (labeled "Prototype screen"); CTAs; transparent nav state; honest DemoModal (Radix `Dialog`) with EmailCapture.
Gate: view-source shows the full H1 sentence; reduced-motion shows the static full sentence; CLS≈0; in-page Watch-demo opens the modal; Create-account → `APP_URL/register`.

**Phase 4 — Homepage scroll story.**
Goal: Statement → Meet the Elves (**Inbox + Compliance live; Voice + SMS "Coming soon"/omitted — §10.1**) → How it works (self-assembling mockup, re-pointed to app `ve-*` tokens per §1A/F12) → Role cards → Trust band → Finale (Watch-demo opens modal).
Gate: zero invented copy/claims (every line traceable to a brief/source doc); **no live SMS/voice claim anywhere**; "Prototype screen" labels present; orange ≤5% per viewport; reveals reduced-motion safe; full top-to-bottom pass on desktop + 375px.

**Phase 5 — Role pages (`/agents`, `/client-portal`, `/fsbo`).**
Goal: one shared role template; approved copy; labeled mockups; FAQ + FAQPage JSON-LD; honor all OMIT notes (placeholder quotes excluded); `#teams` placeholder on `/agents`.
Gate: copy traceability; JSON-LD validates; standard a11y/mobile/orange checks.

**Phase 6 — Product · How It Works · Demo · Create Account.**
Goal: `/product` (SoftwareApplication, capability-truth-checked feature list), `/how-it-works` (HowTo), `/demo` (swap-ready player), `/create-account` (noindex, APP_URL only).
Gate: no invented capabilities; demo placeholder honest; APP_URL via config only; schema validates; every CTA destination confirmed.

**Phase 7 — FAQ + Contract-to-Close guide.**
Goal: `/faq` (grouped, FAQPage over all Q&As, `#attorneys`) + `/guides/contract-to-close` (HowTo + BreadcrumbList, elf callouts).
Gate: spot-check answers against source; omit conflicting (pricing/live-demo) Qs; anchors resolve.

**Phase 8 — About · Contact · Legal.**
Goal: factual About (DRAFT), Contact (placeholder email), Legal scaffolds (DRAFT).
Gate: no invented facts; DRAFT markers; Jan/Jake review the drafted copy; reused EmailCapture unchanged.

**Phase 9 — SEO/AEO finalization.**
Goal: sitewide unique titles/descriptions/canonicals/OG + branded OG image; Organization+WebSite JSON-LD on home; `sitemap.xml` + `robots.txt`; answer blocks verified; internal-link audit (every page ≤2 clicks from home; no dead hrefs).
Gate: page-by-page metadata table; all JSON-LD validates at validator.schema.org; zero broken links.

**Phase 10 — QA, performance & decoupled deploy.**
Goal: Lighthouse on every page (mobile Perf ≥90, SEO=100, A11y ≥95 — report actuals); keyboard-only pass; 375px review of every page; champagne sweep; static-export verification; deploy to its **own** S3/CloudFront staging distribution behind `stage.velvetelves.com`.
Gate: the non-dev UAT script (§12.1) passes end-to-end on a real phone + desktop; score table; fix list cleared; working staging URL.

**Phase 11 (post-v1, parked) — video hero & the rest of the §16 backlog** — only if Jake greenlights the activity-video hero.

---

## 12. Testing & validation strategy

### 12.1 Non-developer UAT script (a real-estate tester can run it with a mouse)
A printable click-path checklist, run on a phone and a desktop. Every step is a click + an observation, no dev tools:
1. Open the home page. *See* a calm hero with the rotating headline + a product preview and two buttons. No layout overflow.
2. Click the **in-page Watch demo** (hero) → a modal says the demo is in production and offers to email me when it's ready. Enter an email → *see* "You're on the list." Close. Then click **Watch demo in the top nav** → it opens the **`/demo` page** (same honest message). Both are fine; neither plays a fake video.
3. Click each **role** in the nav (Agents, Brokers & Teams, FSBO, Attorneys) → each lands somewhere real (page or anchor), never a dead end.
4. On `/agents`, scroll the whole page → every section reads cleanly; open two FAQ items. Confirm **no card claims SMS or voice as available today** (they read "Coming soon" if shown at all).
5. As an **Agent**, click **Create an account** → land on the real Velvet Elves sign-up screen, and confirm "Agent" is selectable. As an **FSBO** visitor, the FSBO page's primary action is **Watch demo / Join early access** — it does **not** drop me on a sign-up screen with no FSBO option.
6. Open the footer → click one link in each column → each resolves.
7. Repeat 1–6 on a phone. Nothing is cut off; buttons are tappable; text is legible; CTAs are readable (no faint text on orange).
8. Reduced-motion: enable "reduce motion" on the device → the headline shows the full static sentence, the site is calm and fully readable (no missing content).

### 12.2 Automated / developer gates (per phase)
- `npm run build` (static export) clean; one HTML file per route with H1 + JSON-LD in source.
- `verify-rls.mjs` proves anon insert-only, **after a service-role seed row exists** so the SELECT denial proves RLS rather than an empty table (§1A/F10).
- JSON-LD validates; metadata table within length limits; no dead hrefs (link crawler over `dist/`).
- Lighthouse budgets met; AA contrast on CTAs; champagne ≤5% per viewport.
- **Render + screenshot every page (desktop + 375px) and compare before declaring a phase done** (Jan's standing rule; emulate the app's chrome-devtools review step).

### 12.3 Continuity check
Side-by-side screenshot of the marketing finale CTA → the app `RegisterPage` to confirm the seam is visually seamless (same serif, champagne, calm).

---

## 13. Deployment & operations

- **Build:** `npm run build` → static `dist/`.
- **Host:** dedicated S3 bucket + CloudFront distribution (separate from the app). SPA/static behavior; ensure correct MIME types (the app learned `.mjs` must be served as JavaScript — apply the same care if any worker assets appear).
- **Domains:** `stage.velvetelves.com` (staging) and `velvetelves.com` (prod) per the AWS plan; app stays `app.velvetelves.com`. DNS in GoDaddy now (Route 53 later).
- **Envs:** `VITE_APP_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` per environment; secrets only in `.env.local` (gitignored); the anon key is safe client-side **only because RLS is insert-only** (verify first).
- **Independence:** marketing deploys on its own pipeline; a marketing deploy can never affect the app or its data. Promotion model can mirror the app's `main`=staging / `prod`=production if desired, but in its own workflow.

---

## 14. Risks, open questions, decisions needed

**Q1 — Hero (RESOLVED by audit; one item left for Jake).** v1 keeps the locked rotating tagline and adds the command-center mockup in a split layout (§1A/F3) — no decision needed there. The only open item: does Jake want the **full-bleed activity video** as a later enhancement, or is the mockup the permanent hero? (Video is post-v1 either way.)
**Q2 — Marketing Supabase project.** Reuse Jake's existing marketing project (`mooktjgryaozlbaxgmei`) or stand up a fresh marketing-only project for `velvet-elves-marketing-new`? Either keeps decoupling; pick one before Phase 2.
**Q3 — Role-prefill + FSBO/Attorney sign-up (RESOLVED for v1; needs app work to improve).** The app's `RegisterPage` reads no `?role` param (§1A/F5) and FSBO/Attorney aren't in `ACCOUNT_TYPES_NOW` (§1A/F4). v1 therefore links to plain `/register` and routes FSBO/Attorney to early-access. *Decision for later:* whether to (a) add `?role` reading to `RegisterPage`, and (b) bring FSBO/Attorney self-sign-up forward — both are **app-side changes**, separate from this marketing build, and they unlock those audiences' "Create an account" CTA.
**Q4 — Voice/SMS Elf (RESOLVED by audit; confirm the scope call with Jake).** Confirmed **not shipped** (§1A/F1), so v1 marks them "Coming soon"/omits them. This **overrides Jake's locked decision #9** ("all four live"). Confirm Jake accepts the honest treatment rather than waiting to launch marketing until the Twilio/voice adapter (Phase 6/7) lands.
**Q5 — Contact email + About/Legal copy.** Real contact address; Jake's approval of the About draft; attorney review of Legal before launch.
**Q6 — Analytics.** Jake left analytics "TBD." Decide a privacy-respecting analytics choice (or none) before prod; reflect it in `/legal`.
**Q7 — Wordmark/logo asset.** Use `velvet-elves-data/logo.png` / the app's `velvet-elves-icon.svg`, or a marketing-specific lockup? Confirm before Phase 1.

**Risks & mitigations.** *Prerender friction with `vite-react-ssg`* → spike it in Phase 0; React Router 7 framework-mode prerender is the fallback. *Design drift from the app* → tokens are copied, never retyped; screenshots compared each phase. *Honesty drift* → the §10 capability truth-check is a hard gate. *Scope creep* → 13 pages only; the §16 backlog is explicitly out of v1.

---

## 15. Definition of done (v1 launch checklist)

- [ ] All 13 pages built, static-exported, each with H1 + correct metadata + JSON-LD in view-source.
- [ ] Tokens/fonts ported verbatim from the app; brand reads as one product into the sign-up screen (continuity screenshot attached).
- [ ] Non-dev UAT script (§12.1) passes end-to-end on a real phone and desktop.
- [ ] `EmailCapture` proven insert-only; no other data collected; secrets gitignored.
- [ ] Lighthouse: mobile Perf ≥90, SEO=100, A11y ≥95 (actuals recorded per page).
- [ ] Champagne ≤5%/viewport; AA on CTAs; reduced-motion paths everywhere; 375px clean.
- [ ] Every claim truth-checked against the real product (§10/§10.1); zero invented proof; mockups labeled "Prototype screen." **No page claims SMS or Voice as live; `featureList`/JSON-LD exclude them (§1A/F1).**
- [ ] All CTAs resolve with no dead ends; in-page Watch-demo → modal, nav Watch-demo → `/demo` (§1A/F2); "Create an account" → real `/register` **only for self-sign-up roles**; FSBO/Attorney → early-access, never an excluding register screen (§1A/F4); no dead hrefs.
- [ ] Deployed to its own staging S3/CloudFront at `stage.velvetelves.com`, independent of the app.
- [ ] Open questions Q1–Q7 resolved or explicitly deferred with Jake.

---

## 16. Post-v1 backlog (out of scope for this build)

Brokers & Teams page · Attorneys page · TC page · Vendor page · remaining educational guides (Dry vs Wet, Timelines, Title vs Lien) · ListedKit comparison (needs proof assets first) · Blog · activity-video hero swap-in · analytics decision · production-domain cutover to `velvetelves.com` · Route 53 migration.

---

*End of plan. This document is strategy and specification only; no application source was created or modified in producing it.*
