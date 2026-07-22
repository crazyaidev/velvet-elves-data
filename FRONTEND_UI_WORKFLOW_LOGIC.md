# Velvet Elves — Frontend UI Workflow Logic Specification

**Version:** 1.1
**Date:** 2026-05-09
**Scope:** Complete page-by-page frontend workflow logic for all routes
**Reference Designs:** 10 approved HTML designs in `completed_designs/`
**Status:** Live as-built spec — sections 2.1 (Onboarding), 6.3 (Settings), 6.4 (AI Email Review), and §14.10 (Product Tour) have been rewritten to match the May 2026 implementation. Other sections still reflect the pre-Phase-3 design review and may drift from the build.

---

## Table of Contents

1. [Auth Pages](#1-auth-pages)
2. [Onboarding](#2-onboarding)
3. [Dashboard Landing Pages](#3-dashboard-landing-pages)
4. [Deals Section](#4-deals-section)
5. [Workflow Section](#5-workflow-section)
6. [Intelligence Section](#6-intelligence-section)
7. [Attorney Workspace](#7-attorney-workspace)
8. [FSBO Customer Workspace](#8-fsbo-customer-workspace)
9. [Client Portal](#9-client-portal)
10. [Admin Section](#10-admin-section)
11. [Profile](#11-profile)
12. [Shared / Public](#12-shared--public)
13. [Cross-Cutting Workflows](#13-cross-cutting-workflows)
14. [Global Interaction Patterns](#14-global-interaction-patterns)
15. [Constraints & Rules](#15-constraints--rules)

---

## Shared Shell Reference

All internal pages share a common app shell. This section defines it once; individual page sections reference it by name.

### Internal Shell

- **Topbar (58px):** Brand lockup + AI indicator | "Today's AI Briefing" chip (Critical / Needs Attention / On Track counts — clickable as filter shortcuts) | Global search input | Notification bell | User avatar chip (click opens menu: Settings, Log out) | Contextual CTA (e.g., "+ New Transaction")
- **Left Sidebar (220px, dark navy `#1E3356`):** work + record-review only. All configuration lives in the Settings hub (NAVIGATION_AND_SETTINGS_CONSOLIDATION_SUPERIOR_PLAN.md).
  - 2×2 KPI tiles (role-specific; default for Agent: Overdue Tasks, Closing This Week, Active Deals, Pipeline Value)
  - Navigation groups:
    - **Dashboard** — role-specific landing
    - **Deals** — Active Transactions (badge), Pending (badge), Closed, All Transactions, Clients
    - **Workflow** — My Task Queue (badge), All Documents, Closing Calendar
    - **Payments** — Invoices & Payments, Commission Payouts (when permitted)
    - **Vendors** — Vendor Directory
    - **Intelligence** — AI Suggestions (badge), AI Email Review (badge), Vendor Proposals (badge), Analytics
    - **Team** (Team Lead + Admin) — Team Overview
    - **Oversight** (Admin) — Communication Audit, Audit Log
  - Footer: Pinned "+ New Transaction" CTA button | User profile card (avatar, name, role; click opens menu: **Settings**, Log out)
- **Settings hub (`/settings`):** opened from the avatar-menu Settings entry. One card-grid surface, role-filtered, in two scope groups:
  - **Personal Settings** (every internal role): Account, Notifications, Email & E-signature (per-user inbox + DocuSign), Email Templates, My Playbook, Help & Tour.
  - **Workspace Settings** (Admin / Owner; team library shared with Team Lead): Company, Branding, Billing & Credits, Users & Invites, Teams, Task Templates, Vendor Templates, Team Playbook, Integrations & Webhooks, AI & Automation, Payment Access, Advertising, Delete Organization.
  - Portal roles (Client / FSBO / Vendor) keep the lightweight Account modal instead of the hub.
- **Page Header:** Title + count pill | Action buttons (Export CSV, Print Report) | Tab bar (page-level filter tabs with live counts) | Sort control + inline search
- **Content Area:** Scrollable, padded, receives primary page content

### FSBO / Client Shell

- Simplified sidebar: Dashboard, My Properties, Documents, Milestones & Messages, Ask Velvet Elves AI, Notifications, Sharing
- Topbar: Brand lockup | "Share milestones" CTA (FSBO) | Notification bell | User chip
- No internal workflow navigation (Deals, Workflow, Intelligence groups hidden)

---

# 1. Auth Pages

---

## 1.1 Login — `/login`

### 1. Page Identity & Access
- **Route:** `/login`
- **Page title:** "Sign In to Velvet Elves"
- **Allowed roles:** Public (unauthenticated users)
- **Redirect rule:** If user is already authenticated, redirect to `/dashboard`
- **Auth requirement:** Public

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** User must NOT be authenticated. If a valid JWT exists in storage, redirect to `/dashboard`.
- **API endpoints consumed on mount:**
  - `GET /api/v1/tenants/by-domain` — resolve current domain to tenant for branding (logo, colors)
- **Loading state UI:** Centered spinner over blank branded page until tenant branding resolves
- **Empty state UI:** N/A
- **Error state UI:** If tenant resolution fails, display default Velvet Elves branding with a dismissible warning toast "Unable to load custom branding"

### 3. Layout & Component Hierarchy
- **Shell variant:** No shell — standalone centered card layout with background gradient
- **Sidebar state:** Hidden
- **Topbar state:** Hidden
- **Page header:** Tenant logo (or Velvet Elves default) centered above the form card
- **Primary content area:**
  1. Logo / brand lockup
  2. "Sign in to your account" heading
  3. Email input field
  4. Password input field (with show/hide toggle)
  5. "Remember me" checkbox
  6. "Sign In" primary button (full width)
  7. "Forgot password?" link
  8. Divider — "or continue with"
  9. OAuth buttons (Google, Microsoft) — only if tenant has OAuth configured
  10. "Don't have an account? Contact your administrator" helper text
- **Overlay/modal inventory:** None

### 4. User Actions & State Transitions

**Email input:**
- Trigger: User types in email field
- Immediate UI: Real-time format validation (red border + helper text if invalid email format)
- API call: None
- Success: Field valid state (green check icon)
- Failure: Inline validation error "Please enter a valid email address"

**Password input:**
- Trigger: User types in password field
- Immediate UI: Show/hide toggle icon
- API call: None
- Success: N/A
- Failure: N/A

**"Sign In" button click:**
- Trigger: Click or Enter key
- Immediate UI: Button disabled + spinner, inputs disabled
- API call: `POST /api/v1/auth/login` with `{ email, password }`
- Success: Store JWT + refresh token → check `onboarding_completed` flag → if false redirect to `/onboarding`, else redirect to `/dashboard`
- Failure:
  - 401 Invalid credentials → error toast "Invalid email or password" + shake animation on form
  - 403 Account deactivated → error toast "Your account has been deactivated. Contact your administrator."
  - 429 Rate limited → error toast "Too many attempts. Please try again in X minutes."
  - 5xx → error toast "Something went wrong. Please try again."
- Side effects: Audit log entry `login` (success or failure)

**"Forgot password?" link:**
- Trigger: Click
- Immediate UI: Navigate to `/forgot-password`

**OAuth button click (Google/Microsoft):**
- Trigger: Click
- Immediate UI: Button loading state, redirect to OAuth provider
- API call: Supabase Auth `signInWithOAuth({ provider })`
- Success: OAuth callback at `/auth/callback` handles token exchange → redirect to `/dashboard` or `/onboarding`
- Failure: Return to `/login` with error toast "Authentication failed. Please try again."
- Side effects: Audit log entry

### 5. Conditional Rendering Logic
- **Role-based visibility:** None (public page)
- **State-based visibility:** OAuth buttons render only if tenant `settings_json.oauth_providers` array is non-empty
- **Feature flags:** OAuth providers gated per tenant configuration
- **Responsive behavior:** Card centers horizontally and vertically; on mobile (<640px), card fills full width with padding

### 6. Navigation Flows
- **Inbound routes:** Direct URL entry, logout redirect, unauthorized access redirect (with return URL in query param), invite acceptance redirect
- **Outbound routes:** `/dashboard` (successful login), `/forgot-password`, `/register` (if enabled), `/auth/callback` (OAuth), `/onboarding` (if onboarding not completed)
- **Deep-link support:** `?returnTo=/path` query parameter preserved through login; after successful auth, redirect to returnTo instead of `/dashboard`
- **Back navigation:** Browser back goes to previous page (typically landing page or referrer)

### 7. AI Integration Points
- **AI data on page:** None
- **AI actions available:** None
- **AI confidence display:** None
- **AI guardrails:** N/A
- **AI chat panel:** Not available (unauthenticated)

### 8. Real-Time & Notification Behavior
- **Live updates:** None
- **Notification triggers:** None
- **Toast/alert patterns:** Error toasts for failed login attempts; success is a redirect (no toast)

### 9. Cross-Page Relationships
- **Shared state:** `returnTo` query param stored for post-login redirect
- **Dashboard deep-linking:** N/A
- **Data dependencies:** None — standalone entry point

### 10. Edge Cases & Special Behaviors
- **First-time user:** If arriving via invite link, redirect to `/invite/:token` instead
- **Concurrent sessions:** Allow multiple browser sessions; each stores its own JWT
- **Offline/slow network:** Show retry button after 10-second timeout on login attempt
- **Password manager autofill:** Form fields must use correct `autocomplete` attributes (`email`, `current-password`)
- **CSRF:** Login form protected with CSRF token

---

## 1.2 Register — `/register`

### 1. Page Identity & Access
- **Route:** `/register`
- **Page title:** "Create Your Account"
- **Allowed roles:** Public — typically only accessible via invitation link redirect; direct access may be disabled per tenant
- **Redirect rule:** If already authenticated → `/dashboard`. If tenant disables open registration → redirect to `/login` with toast "Registration is invite-only."
- **Auth requirement:** Public

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** User not authenticated. Tenant allows open registration OR user arrived via invite flow.
- **API endpoints consumed on mount:**
  - `GET /api/v1/tenants/by-domain` — tenant branding
- **Loading state UI:** Centered spinner
- **Empty state UI:** N/A
- **Error state UI:** Default branding if tenant fetch fails

### 3. Layout & Component Hierarchy
- **Shell variant:** Standalone centered card (same as login)
- **Primary content area:**
  1. Logo / brand lockup
  2. "Create your account" heading
  3. Full Name input
  4. Email input (pre-filled if from invite)
  5. Phone input (optional)
  6. Password input with strength indicator
  7. Confirm Password input
  8. "Create Account" primary button
  9. "Already have an account? Sign in" link
- **Overlay/modal inventory:** None

### 4. User Actions & State Transitions

**"Create Account" button click:**
- Trigger: Click or Enter
- Immediate UI: Button disabled + spinner
- API call: `POST /api/v1/auth/register` with `{ full_name, email, phone, password }`
- Success: Confirmation email sent → redirect to `/login` with success toast "Account created! Please check your email to verify."
- Failure:
  - 409 Email exists → inline error "An account with this email already exists"
  - 422 Validation errors → highlight failing fields with inline messages
  - 5xx → error toast
- Side effects: Audit log `create` on `user` entity; invitation token marked as used if applicable

### 5. Conditional Rendering Logic
- **State-based visibility:** If arrived from invite flow, email field is pre-filled and read-only; role badge shown ("You're being invited as an Agent")
- **Responsive behavior:** Same as login page

### 6. Navigation Flows
- **Inbound routes:** `/invite/:token` redirect, direct URL (if open registration enabled), `/login` "create account" link
- **Outbound routes:** `/login` (after creation or via "Sign in" link)
- **Deep-link support:** None
- **Back navigation:** Returns to login or invite page

### 7–8. AI Integration & Real-Time
- None (public page)

### 9. Cross-Page Relationships
- **Data dependencies:** If from invite, the invite token determines pre-filled email, role, and team assignment

### 10. Edge Cases
- **Password strength:** Must enforce minimum 8 characters, one uppercase, one number. Strength bar shows weak/medium/strong.
- **Duplicate tab:** If user completes registration in one tab, the other tab should detect on next action and redirect to login
- **Expired invite:** If invite token is expired or used, show error "This invitation has expired. Please contact your administrator."

---

## 1.3 Forgot Password — `/forgot-password`

### 1. Page Identity & Access
- **Route:** `/forgot-password`
- **Page title:** "Reset Your Password"
- **Allowed roles:** Public
- **Redirect rule:** Authenticated users → `/dashboard`
- **Auth requirement:** Public

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** None
- **API endpoints on mount:** Tenant branding
- **Loading/Empty/Error states:** Same pattern as login

### 3. Layout & Component Hierarchy
- **Shell variant:** Standalone centered card
- **Primary content area:**
  1. Logo
  2. "Forgot your password?" heading
  3. "Enter your email and we'll send you a reset link." subtitle
  4. Email input
  5. "Send Reset Link" primary button
  6. "Back to sign in" link
- **Overlay/modal inventory:** None

### 4. User Actions & State Transitions

**"Send Reset Link" click:**
- Trigger: Click
- Immediate UI: Button disabled + spinner
- API call: `POST /api/v1/auth/forgot-password` with `{ email }`
- Success: Show confirmation state "Check your email" with email icon illustration; "Didn't receive it? Resend" link (cooldown 60 seconds)
- Failure: Always show success state to prevent email enumeration. Log failure internally.
- Side effects: Email sent via Supabase Auth; audit log

### 5–10. Standard Patterns
- **Responsive:** Centered card, full-width on mobile
- **Navigation:** Inbound from `/login`; outbound to `/login` via "Back to sign in"
- **Edge case:** Rate-limit resend button to prevent abuse (60-second cooldown displayed as countdown)

---

## 1.4 Reset Password — `/reset-password`

### 1. Page Identity & Access
- **Route:** `/reset-password`
- **Page title:** "Set New Password"
- **Allowed roles:** Public (with valid reset token in URL hash)
- **Redirect rule:** If token is invalid/expired → redirect to `/forgot-password` with error toast "Reset link has expired. Please request a new one."
- **Auth requirement:** Public + valid Supabase recovery token

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** Valid Supabase recovery token present in URL fragment
- **API endpoints on mount:** Supabase Auth verifies token automatically
- **Loading state UI:** Spinner while token validates
- **Error state UI:** Invalid token → redirect with toast

### 3. Layout & Component Hierarchy
- **Primary content area:**
  1. Logo
  2. "Set your new password" heading
  3. New Password input with strength indicator
  4. Confirm Password input
  5. "Reset Password" primary button

### 4. User Actions & State Transitions

**"Reset Password" click:**
- Trigger: Click
- Immediate UI: Button spinner
- API call: Supabase `updateUser({ password })` using recovery session
- Success: Toast "Password updated successfully" → redirect to `/login`
- Failure: 422 → inline validation; expired token → redirect to `/forgot-password`
- Side effects: Audit log

### 5–10. Standard Patterns
- Same card layout and responsive behavior as other auth pages
- **Edge case:** If user navigates directly without token → redirect to `/forgot-password`

---

## 1.5 OAuth Callback — `/auth/callback`

### 1. Page Identity & Access
- **Route:** `/auth/callback`
- **Page title:** "Completing sign in…"
- **Allowed roles:** Public (OAuth redirect target)
- **Auth requirement:** Public — processes OAuth authorization code

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** OAuth provider redirects here with authorization code in URL
- **API endpoints on mount:**
  - Supabase Auth handles token exchange automatically
  - `GET /api/v1/users/me` — fetch user profile after auth completes
- **Loading state UI:** Full-page centered spinner with "Completing sign in…" text
- **Error state UI:** If auth exchange fails → redirect to `/login` with error toast

### 3. Layout & Component Hierarchy
- **Shell variant:** Blank page — spinner only
- No interactive elements; purely a processing redirect

### 4. User Actions & State Transitions
- **Automatic on mount:**
  - Supabase processes the OAuth callback
  - On success: Check if user exists in `users` table → if new user, create profile → check `onboarding_completed` → redirect to `/onboarding` or `/dashboard`
  - On failure: Redirect to `/login` with error

### 5–10.
- No interactive elements, no navigation controls
- **Edge case:** If user manually navigates here without OAuth state → redirect to `/login`

---

## 1.6 Invite Acceptance — `/invite/:token`

### 1. Page Identity & Access
- **Route:** `/invite/:token`
- **Page title:** "You've Been Invited"
- **Allowed roles:** Public
- **Redirect rule:** If token is invalid/expired/used → `/login` with error toast
- **Auth requirement:** Public

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** Valid, unused invitation token
- **API endpoints on mount:**
  - `GET /api/v1/invitations/:token` — validate token, return `{ email, role, tenant_name, invited_by_name, team_name }`
- **Loading state UI:** Centered spinner "Validating your invitation…"
- **Empty state UI:** N/A
- **Error state UI:** Invalid/expired → redirect to `/login` with toast "This invitation is no longer valid."

### 3. Layout & Component Hierarchy
- **Shell variant:** Standalone centered card
- **Primary content area:**
  1. Logo (tenant-branded)
  2. "You've been invited!" heading
  3. Invitation details card: "[Invited_by] has invited you to join [Tenant] as [Role]"
  4. If team: "You'll be part of the [Team Name] team"
  5. If user has existing account: "Sign In" button (pre-fills email on login page)
  6. If new user: "Create Account" button → redirects to `/register` with token context
- **Overlay/modal inventory:** None

### 4. User Actions & State Transitions

**"Create Account" click:**
- Trigger: Click
- Immediate UI: Redirect to `/register?invite=:token`
- The register page pre-fills email, displays role badge, and on successful registration marks the invitation as used and assigns the user to the specified tenant/team/role

**"Sign In" click:**
- Trigger: Click
- Immediate UI: Redirect to `/login?invite=:token`
- After login, system checks if invitation token is still valid and applies the role/team assignment

### 5–10. Standard Patterns
- **Edge case:** If user is already authenticated and visits invite link for a different tenant → prompt "You're currently signed in as [email]. Sign out to accept this invitation?"
- **Expired token:** Show friendly message with "Contact [invited_by] to request a new invitation" guidance

---

# 2. Onboarding

---

## 2.1 Onboarding — `/onboarding`

> **As-built (May 2026):** the wizard is now fully role-branched, OAuth-driven, and hands off completion to either the dashboard or a nested New Transaction wizard. This section reflects the live implementation in `OnboardingWizard.tsx`; the previous spec described a planned 6–7-step variant that was cut.

### 1. Page Identity & Access
- **Route:** `/onboarding`
- **Page title:** "Set up your workspace"
- **Allowed roles:** All authenticated roles where `onboarding_completed === false`
- **Redirect rule:** On mount the wizard calls `GET /api/v1/onboarding/status`; if the server reports onboarding is already finished, replace-navigate to `/dashboard` before any step renders. If unauthenticated → `/login`.
- **Auth requirement:** Protected. Forwarded to from `RegisterPage` (post sign-up), `InviteAcceptPage` (post invite acceptance), and `AuthLayout` on every login/refresh until `onboarding_completed === true`.

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** User authenticated.
- **API endpoints on mount:**
  - `GET /api/v1/users/me` — current user profile (name, phone, role, company, logo URL).
  - `GET /api/v1/onboarding/status` — bounce-out check (single-shot via `bounceCheckRef` to avoid race against the user's own "complete" click).
- **Loading state UI:** Brief spinner over the dark-rail layout until `/me` resolves.
- **Empty state UI:** N/A.
- **Error state UI:** Destructive toast on save failure; user stays on the current step.

### 3. Layout & Component Hierarchy
- **Shell variant:** Standalone full-page. Dark left rail (logo, vertical numbered stepper, privacy blurb) + white right panel with the active step's content. Mobile collapses the rail into a thin orange progress strip across the top.
- **Footer:** **Back** (left, disabled on step 1) + **Continue** / **Skip for now** (right). Final step hides the footer.
- **Step list is computed live from `user.role`:**

  - **Internal roles** (Agent, Transaction Coordinator, Team Lead, Attorney, Admin): 4–5 steps.
  - **External roles** (Client, FSBO, Vendor, anything not internal): 3 steps.

**Step content (in order):**

1. **Welcome (all roles).** Personalized greeting (`Hi {firstName}, let's set up your workspace`), role-specific intro line, and 2–4 value cards. Internal roles see four cards (Tell us about you, Connect inbox, E-sign with DocuSign, Land in dashboard); external roles see only the first and last. **Let's go** primary button advances. No Back. No Skip.

2. **Your Profile (all roles).**
   - Full name (text, prefilled from `/me`).
   - Phone (tel, optional, auto-formats to `(555) 123-4567` on display, digit-only on submit).
   - Role dropdown — every value in `USER_ROLES`. Changing it rebuilds the step list live; switching from internal → external mid-flow shrinks the wizard from 4–5 steps to 3, and the active index is clamped so the user does not fall off the end. A hint appears under the dropdown: "You'll be updated to this role after this step."
   - **Internal roles only:** Company / brokerage (text), Brand logo drag-drop zone with preview, Upload/Replace + Remove buttons. Logo rules: PNG/JPEG/WEBP/SVG/GIF, ≤ 2 MB. Wrong type or oversize → destructive toast, no upload. Optimistic preview rendered via FileReader; reverts to prior URL on API failure.
   - **Continue** persists the step before advancing (validation-by-save):
     - `PATCH /api/v1/users/me` (name, phone)
     - `PATCH /api/v1/onboarding/company` (company, role)
     - `POST /api/v1/onboarding/logo` multipart on logo upload, or `PATCH /api/v1/onboarding/logo` with empty URL on Remove.
   - Button shows "Saving…" with a spinner while the calls run; on any failure the wizard stops at this step.

3. **Email Inbox (internal roles only).**
   - Two provider cards: **Gmail** (Google OAuth) and **Outlook** (Microsoft 365 OAuth).
   - Connection runs through `useEmailProviderOAuth` — real OAuth popup; on success the integration list re-fetches and the card flips to a green "Connected" badge. Cancel/error → destructive toast; card stays in the unconnected state.
   - Bottom safety blurb mentions Fernet-encrypted-at-rest tokens and the ability to disconnect from Settings.
   - **Skip for now** advances without connecting (real toast confirms).

4. **E-signature (Agent / TC / Team Lead / Attorney only — Admin and external roles do NOT see this step).**
   - Single DocuSign provider card (same widget pattern). Live OAuth via `useDocuSignOAuth`.
   - **Skip for now** is allowed.

5. **Final — All set (all roles).**
   - Confetti burst (28 animated particles, plays once), party-popper badge, `You're all set, {firstName}.` headline, animated subhead.
   - **Internal roles** see two action cards:
     1. **Create your first transaction** (primary, "Recommended" kicker) — opens the full `NewTransactionModal` layered on top of the onboarding screen. Onboarding is NOT marked complete until that wizard either creates a transaction (then redirects to `/transactions?highlight={id}`) or is dismissed.
     2. **Go straight to your dashboard** ("Or" kicker).
   - **External roles** see only the dashboard card (relabelled "Recommended").
   - Either CTA calls `POST /api/v1/onboarding/complete`, calls `markTourPending()` so `AppLayout` fires the product tour on the next mount, then `navigate(replace: true)`. Failure → destructive toast; user stays on the screen.

- **Overlay/modal inventory:** `NewTransactionModal` may render layered on the final step.

### 4. User Actions & State Transitions

**Continue button (each step except the final):**
- Trigger: Click.
- Immediate UI: Button shows "Saving…" with spinner; fields disabled.
- API calls: per-step (see step content above).
- Success: Animate slide to next step; rail highlights advance.
- Failure: Destructive toast; stay on current step; Continue button re-enables.

**Stepper rail click:**
- Trigger: Click a previous step in the rail.
- Immediate UI: Jump backward (clears local edits not yet saved on the current step).
- Forward jumps in the rail are intentionally **blocked** — users must click Continue so saves run.

**Skip for now (Email + E-signature steps):**
- Trigger: Click.
- Immediate UI: Toast confirms ("You can connect Gmail / DocuSign later from Settings"); advance to the next step.
- No API call.

**Provider OAuth card (Gmail / Outlook / DocuSign):**
- Trigger: Click an unconnected card.
- Immediate UI: Spinner overlay; OAuth popup opens.
- Success: Integration list refetched; card flips to green "Connected" badge; toast confirms.
- Failure / cancel: Destructive toast; card stays unconnected.

**Logo upload (Step 2, internal roles):**
- Trigger: Drop a file or click "Upload logo".
- Immediate UI: Optimistic FileReader preview.
- API call: `POST /api/v1/onboarding/logo` (multipart).
- Failure: Revert preview to prior URL; destructive toast.
- Remove: `PATCH /api/v1/onboarding/logo` with empty URL → preview cleared.

**Final step CTAs (Create your first transaction / Go to dashboard):**
- Trigger: Click.
- API call: `POST /api/v1/onboarding/complete` (idempotent).
- Side effects: Set `onboarding_completed: true` on the user, call `markTourPending()` (writes session-scoped `velvet_elves_tour_pending` flag).
- Success — Dashboard CTA: `navigate('/dashboard', { replace: true })`.
- Success — Create-your-first-transaction CTA: open `NewTransactionModal`; on transaction creation `navigate('/transactions?highlight={id}', { replace: true })`. If the modal is dismissed without creating, onboarding is still marked complete and user lands on `/dashboard`.

### 5. Conditional Rendering Logic
- **Role-based visibility:**
  - Email step (3) and E-signature step (4) hidden for external roles. Admin sees email but NOT e-signature.
  - "Create your first transaction" final-step CTA shown to internal roles only; external roles see Dashboard CTA labelled "Recommended".
  - Welcome step value cards (4 for internal, 2 for external).
- **State-based visibility:** Logo Remove button only renders once a logo URL is set. Provider cards show green "Connected" badge + disabled state when integration is already linked.
- **Responsive behavior:** Mobile collapses the dark rail into an orange progress strip; primary CTA cards on the final step stack vertically below 768px.

### 6. Navigation Flows
- **Inbound routes:** `RegisterPage` post-signup, `InviteAcceptPage` post-invite, `AuthLayout` redirect on login when `onboarding_completed === false`.
- **Outbound routes:** `/dashboard` (replace), `/transactions?highlight={id}` (replace, after Create your first transaction).
- **Deep-link support:** None — always starts at Step 1 on refresh. Field values auto-rehydrate from `/me`, but the active step index is not persisted.
- **Back navigation:** Browser back goes to the prior page (typically nothing, since this is replace-navigated to). Within the wizard, the rail allows backward jumps and the footer Back button advances backward one step.

### 7. AI Integration Points
- **AI data on page:** None during onboarding itself. The nested `NewTransactionWizard` (opened from the final-step "Create your first transaction" CTA) does include AI document parsing — see §13.A.
- **AI actions available:** None on this page.
- **AI chat panel:** Not available.

### 8. Real-Time & Notification Behavior
- **Live updates:** None.
- **Notification triggers:** None.
- **Toast/alert patterns:** Destructive toasts for save / OAuth / logo failures. Success toasts for integration connections and skip clicks.

### 9. Cross-Page Relationships
- **Shared state:** Profile data saved here flows into the topbar avatar, sidebar profile card, and `/profile` page. Logo URL flows into tenant-branded surfaces.
- **Hand-off to product tour:** `markTourPending()` writes `sessionStorage.velvet_elves_tour_pending = "1"`. `AppLayout` consumes that flag on next mount and immediately auto-starts the role-aware product tour (see §14.10).
- **Hand-off to NewTransactionModal:** the modal is launched from this screen but is the same component used by the rest of the app — see §13.A for full spec.

### 10. Edge Cases
- **Browser refresh mid-wizard:** Field values rehydrate from `/me`; the wizard restarts at Step 1. There is no "finish later" bookmark.
- **Forward jump in rail:** Blocked by design — Continue must run save first.
- **External-role mid-flow switch:** Picking an external role at Step 2 collapses the step list (4–5 → 3); the active step index is clamped so the user is never stranded past the new end.
- **Provider already connected:** Card renders pre-disabled with the green "Connected" badge — no popup is launched.
- **Bounce-out race:** `bounceCheckRef` ensures the `/onboarding/status` check fires only once per mount, preventing a self-redirect when the user finalizes onboarding.
- **`NewTransactionModal` dismissed without creating:** Onboarding still marks complete (idempotent) and the user lands on `/dashboard`.
- **Confetti accessibility:** Plays once; users with `prefers-reduced-motion` see a static badge instead of the burst (Framer Motion respects the system setting).

---

# 3. Dashboard Landing Pages

---

## 3.1 Dashboard Router — `/dashboard`

### 1. Page Identity & Access
- **Route:** `/dashboard`
- **Page title:** N/A (redirect only)
- **Allowed roles:** All authenticated roles
- **Redirect rule:**
  - Agent (solo, no team) → `/dashboard/agent`
  - Agent/Elf on a team, Team Lead → `/dashboard/team`
  - Attorney → `/dashboard/attorney`
  - Admin → `/dashboard/admin`
  - Client → `/client/transactions`
  - FSBO Customer → `/fsbo`
  - Vendor → `/vendor` (the Vendor portal owns the vendor surface; the old
    `/client/documents` vendor hijack was removed — that route is Client-only)
- **Auth requirement:** Protected

This is a pure redirect route. No UI rendered.

---

## 3.2 Solo Agent Dashboard — `/dashboard/agent`

**Design reference:** `completed_designs/ve-homepage_dashboard-solo_agent.html`

### 1. Page Identity & Access
- **Route:** `/dashboard/agent`
- **Page title:** "Dashboard"
- **Allowed roles:** Agent (solo — no team_id), Elf (standalone)
- **Redirect rule:** If user has `team_id` → `/dashboard/team`. Non-agent roles → `/dashboard` for re-routing.
- **Auth requirement:** Protected + role check

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** Authenticated, `onboarding_completed === true`, role is Agent or standalone Elf
- **API endpoints consumed on mount:**
  - `GET /api/v1/dashboard/agent` — aggregated dashboard payload:
    - `health_score` (0–100), `health_descriptor` (text)
    - `action_queue[]` — ranked transactions needing intervention today
    - `drift_diagnostics[]` — reasons deals are drifting
    - `fast_filter_counts` — { critical_closings, missing_responses, stale_communication, document_blockers }
    - `production_snapshot` — { pending_gci, pending_volume, closings_ytd, closings_lifetime, active_count }
    - `priority_transactions[]` — top transactions with next-step CTA, tasks, dates, contacts
    - `ai_intelligence` — portfolio insights, missing-doc concentration, recent communication highlights
  - `GET /api/v1/ai/briefing` — { critical, needs_attention, on_track } counts for topbar
  - `GET /api/v1/transactions/kpi` — sidebar KPI tile data (overdue_tasks, closing_this_week, active_deals, pipeline_value)
- **Loading state UI:** Command grid skeleton: large placeholder card for hero, two smaller placeholders for production/overview. Sidebar KPI tiles show animated pulse placeholders. Topbar briefing chip shows "Loading…"
- **Empty state UI:** If zero transactions: Hero card replaced with "Get started" card — "Create your first transaction to see your dashboard come to life" with prominent "+ New Transaction" CTA and document drag-drop zone
- **Error state UI:** Failed API → error banner at top of content area "Unable to load dashboard data" with Retry button; cached stale data shown if available

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell (sidebar + topbar)
- **Sidebar state:** "Dashboard" nav link active; KPI tiles show: Overdue Tasks (red if > 0), Closing This Week, Active Deals, Pipeline Value
- **Topbar state:** AI briefing chip with live counts; "+ New Transaction" CTA button visible; global search scoped to all
- **Page header:** "Dashboard" title; no tabs; no count pill
- **Primary content area (command grid layout — 3-column: 1.55fr / 0.95fr / 0.8fr):**

  **Row 1: Upload Intake Card (full width)**
  - Drag/drop zone: "Drop a contract or MLS listing to start a new transaction"
  - "Browse files" link
  - AI indicator text: "AI will read your documents and set up the transaction"

  **Row 2: Command Grid**
  - **Column 1 — Hero Card:**
    - Health score ring (conic-gradient, 0–100) with numeric score centered
    - Health descriptor text (e.g., "Strong — 2 items need attention")
    - Action queue: ranked list of transactions needing intervention with one-line reason and clickable link
    - Drift diagnostics: "Why deals are drifting" section with categorized reasons
    - Fast filter buttons: Critical Closings, Missing Responses, Stale Communication, Document Blockers — each shows count, each deep-links to `/transactions/active` with pre-applied filter
  - **Column 2 — Production Snapshot:**
    - Pending GCI (currency, mono font)
    - Pending Volume (currency, mono font)
    - Closings YTD / Lifetime (counts, mono font)
    - Active Transactions count
  - **Column 3 — Transaction Overview:**
    - Closing Soon cards
    - In Inspection cards
    - Documents Needed cards
    - Each shows property address, client name, key metric, and clickable link to transaction

  **Row 3: Priority Transaction Cards (full width, scrollable)**
  - Per-card: client name, address, status pill, next-step CTA button, key tasks (overdue highlighted), key dates, primary contact, footer actions (View Docs, Print Checklist, History)

  **Side Rail (right, overlays or below on narrower screens):**
  - AI Portfolio Intelligence: text insights about portfolio trends
  - Missing-Doc Concentration: which transactions have the most missing documents
  - Recent Communication Highlights: last 5 notable communications

- **Overlay/modal inventory:**
  - New Transaction quick-create modal (triggered by "+ New Transaction" CTA or file drop)
  - AI Chat panel (floating, triggered by AI indicator in topbar or chat icon)

### 4. User Actions & State Transitions

**File drop on upload intake card:**
- Trigger: Drag document over intake card, drop
- Immediate UI: Drop zone highlights on drag-over (dashed border, champagne glow); on drop, shows "AI is reading your document…" with progress spinner
- API call: `POST /api/v1/documents/intake` with file → `POST /api/v1/ai/parse-document`
- Success: Opens New Transaction quick-create modal with AI-extracted fields pre-filled
- Failure: Toast "Unable to read document. Please try again or enter details manually." → opens empty quick-create modal
- Side effects: Document stored in temp storage; audit log

**Fast filter button click (e.g., "Critical Closings"):**
- Trigger: Click
- Immediate UI: Navigate to `/transactions/active?filter=critical`
- No API call on this page; Active Transactions page loads with filter applied

**Action queue transaction link click:**
- Trigger: Click on a transaction row in the action queue
- Immediate UI: Navigate to `/transactions/active?highlight=:transactionId`
- Active Transactions page scrolls to and expands that transaction card

**Priority transaction card "View Docs" click:**
- Trigger: Click
- Immediate UI: Opens Transaction Documents modal for that transaction

**Priority transaction card "Print Checklist" click:**
- Trigger: Click
- Immediate UI: Opens print dialog with closing checklist (Buyer or Seller template from profile, injected tagged notes, escrow overage reminders for sellers)
- API call: `GET /api/v1/transactions/:id/checklist` → returns populated checklist
- Success: Browser print dialog
- Failure: Toast "Unable to generate checklist"

**Priority transaction card "History" click:**
- Trigger: Click
- Immediate UI: Opens Transaction History side panel for that transaction

**KPI tile click (sidebar):**
- Trigger: Click on "Overdue Tasks" tile
- Immediate UI: Navigate to `/transactions/active?filter=overdue`

**AI briefing chip click (topbar):**
- Trigger: Click on "Critical" count
- Immediate UI: Navigate to `/transactions/active?filter=critical`

**"+ New Transaction" CTA click:**
- Trigger: Click
- Immediate UI: Opens New Transaction quick-create modal
- See Cross-Cutting Workflow A for full modal spec

### 5. Conditional Rendering Logic
- **Role-based visibility:** This page only renders for solo Agent/standalone Elf. If user has `team_id`, they see Team Leader Dashboard instead.
- **State-based visibility:**
  - Upload intake card always visible
  - If zero transactions: show empty-state hero instead of command grid
  - Fast filter buttons show counts; buttons with count 0 are still visible but muted
  - AI Portfolio Intelligence section hidden if fewer than 3 transactions
- **Feature flags:** AI Coach placeholder card (future paid feature, $79/mo) may appear as a locked/teaser card in the side rail
- **Responsive behavior:**
  - Desktop (≥1280px): 3-column command grid
  - Tablet (768–1279px): 2-column, side rail moves below main content
  - Mobile (<768px): Single column stack, priority cards become horizontally scrollable

### 6. Navigation Flows
- **Inbound routes:** `/dashboard` redirect, sidebar "Dashboard" link, login redirect, direct URL
- **Outbound routes:**
  - Fast filters → `/transactions/active?filter=X`
  - Action queue items → `/transactions/active?highlight=:id`
  - Priority card links → `/transactions/:id`
  - Sidebar links → respective pages
  - "+ New Transaction" → modal (then redirects to `/transactions/active` or `/transactions/:id` after creation)
- **Deep-link support:** None (dashboard is a summary view, not filterable by URL)
- **Back navigation:** Standard browser back; no breadcrumbs on dashboard

### 7. AI Integration Points
- **AI data on page:**
  - Health score (AI-computed from transaction states, task statuses, communication recency)
  - Action queue ranking (AI-prioritized)
  - Drift diagnostics (AI-analyzed)
  - AI Portfolio Intelligence sidebar (AI-generated insights)
  - AI next-step CTAs on priority transaction cards
  - Topbar AI briefing counts
- **AI actions available:**
  - Document intake parsing (via file drop)
  - AI chat panel (floating) — contextual to portfolio; quick-action prompts: "Show overdue tasks", "What should I focus on today?", "Summarize my pipeline"
- **AI confidence display:** Health score ring implicitly reflects AI confidence; no explicit confidence badges on dashboard
- **AI guardrails:** AI cannot auto-create transactions or auto-send communications from dashboard; all AI suggestions route through human confirmation
- **AI chat panel:** Available — receives user's full transaction portfolio as context

### 8. Real-Time & Notification Behavior
- **Live updates:**
  - AI briefing counts refresh via polling (60-second interval) or Supabase Realtime subscription on `transactions` and `tasks` tables
  - KPI tiles refresh on same cadence
  - If another user completes a task on a shared transaction, action queue updates on next poll
- **Notification triggers:** None generated from dashboard view (read-only surface)
- **Toast/alert patterns:** Error toasts for failed data loads; no success toasts on dashboard (data refresh is silent)

### 9. Cross-Page Relationships
- **Shared state:** Selected filters persist when navigating to Active Transactions (e.g., clicking "Critical Closings" sets the Active Transactions page to "Critical" filter)
- **Dashboard deep-linking:** Every card, filter button, and action queue item deep-links into Active Transactions or Transaction Detail — no dead-end pages
- **Data dependencies:** Dashboard requires at least one transaction to show meaningful data; empty state guides user to create first transaction

### 10. Edge Cases
- **First-time user:** After onboarding, dashboard shows empty state with "Create your first transaction" guidance. If the user hasn't completed their profile (checklist templates missing), a banner prompts: "Complete your profile to enable closing checklists" with link to `/profile`.
- **Large transaction count (50+):** Priority cards limited to top 5 by urgency; "View all" link to Active Transactions. Action queue shows top 10.
- **All deals on track:** Hero card shows high health score; action queue empty with message "All deals are on track! Focus on prospecting or take a break."
- **AI chat triggered from dashboard:** Chat receives portfolio-level context (not a specific transaction)

---

## 3.3 Team Leader Dashboard — `/dashboard/team`

**Design reference:** `completed_designs/ve-homepage_dashboard-team_leader.html`

### 1. Page Identity & Access
- **Route:** `/dashboard/team`
- **Page title:** "Team Dashboard"
- **Allowed roles:** Team Lead, Agent with `team_id`, Elf with `team_id`
- **Redirect rule:** Users without `team_id` → `/dashboard/agent`. Non-internal roles → `/dashboard`.
- **Auth requirement:** Protected + team membership check

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** Authenticated, onboarding complete, user belongs to a team
- **API endpoints consumed on mount:**
  - `GET /api/v1/dashboard/team` — aggregated team dashboard:
    - `team_health_score` (0–100), `team_health_descriptor`
    - `intervention_queue[]` — transactions ranked by likelihood of breaking
    - `drift_metrics` — { closings_7day_unresolved, no_client_touch_72h, missing_signatures, agents_needing_coaching }
    - `agent_board[]` — per-agent summary (active deals, overdue tasks, upcoming closings, health score)
    - `team_financials` — { pipeline_health, annual_pace, pending_gci, pending_volume }
    - `closings_next_14_days[]` — upcoming closing list
  - `GET /api/v1/ai/briefing?scope=team` — team-scoped briefing counts
  - `GET /api/v1/transactions/kpi?scope=team` — team KPI tiles
- **Loading state UI:** Same skeleton pattern as Solo Agent but with team-specific placeholders
- **Empty state UI:** If team has zero transactions: "Your team hasn't started any transactions yet" with "+ New Transaction" CTA
- **Error state UI:** Error banner with retry

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell with Team Lead sidebar additions
- **Sidebar state:** "Dashboard" active; additional "Team" section with "Agents" and "Task Templates" links. KPI tiles: Team Overdue Tasks, Team Closings This Week, Team Active Deals, Team Pipeline Value.
- **Topbar state:** AI briefing chip shows team-aggregated counts; "+ New Transaction" CTA
- **Page header:** "Team Dashboard" title; toggle switch: "My Deals" | "Team View" (default: Team View for Team Lead, My Deals for Agent/Elf)
- **Primary content area (command grid layout):**

  **Row 1: Upload Intake Card** (same as Solo Agent)

  **Row 2: Command Grid (3-column)**
  - **Column 1 — Team Hero Card:**
    - Team health score ring
    - Intervention queue (ranked by breaking likelihood): transaction name, agent name, risk reason, days to close
    - Drift/discipline metrics: closings in 7 days with unresolved deps, no client touch 72+ hrs, missing signatures/doc gaps, agents needing coaching
    - Fast filter buttons: same as Solo Agent but team-scoped
  - **Column 2 — Team Performance:**
    - Agent board: each agent as a compact row (avatar, name, active deals, overdue, health indicator) — click to drill down
    - Team financials: pipeline health, annual pace, pending GCI, pending volume
  - **Column 3 — Upcoming Activity:**
    - Closings in next 14 days (list with dates, agent names, status indicators)

  **Side Rail:**
  - AI Portfolio Intelligence (team-scoped)
  - Coach prompts (e.g., "Agent X has 3 deals closing next week with missing docs — consider a check-in")
  - Documents blocking milestones
  - Recent communication highlights

- **Overlay/modal inventory:**
  - New Transaction quick-create modal
  - AI Chat panel
  - Agent drill-down modal/page (click agent row → see their full portfolio)

### 4. User Actions & State Transitions

**"My Deals" / "Team View" toggle:**
- Trigger: Click toggle switch
- Immediate UI: Content refreshes to show personal or team-scoped data
- API call: Same endpoints with `?scope=personal` or `?scope=team` parameter
- Success: Grid data updates; KPI tiles update; briefing counts update
- Failure: Toast; fall back to previous view

**Agent board row click:**
- Trigger: Click on an agent's row
- Immediate UI: Navigate to `/transactions/active?agent=:agentId` (filtered by that agent)
- Shows all of that agent's transactions in Active Transactions workspace

**Intervention queue item click:**
- Trigger: Click
- Immediate UI: Navigate to `/transactions/active?highlight=:transactionId`

**Drift metric click (e.g., "No client touch 72+ hrs: 4"):**
- Trigger: Click
- Immediate UI: Navigate to `/transactions/active?filter=stale_communication`

### 5. Conditional Rendering Logic
- **Role-based visibility:**
  - Team Lead: sees full intervention queue, agent coaching indicators, task template management links
  - Agent on team: sees "My Deals" by default; can toggle to "Team View" (read-only team overview); cannot see coaching indicators for other agents
  - Elf on team: same as Agent on team but with elf-specific task queue emphasis
- **State-based visibility:**
  - AI Coach placeholder card: shown but locked ("Coming Soon — $79/agent/month") — not functional in MVP
  - Agent board: only visible in "Team View" mode
- **Responsive behavior:** Same breakpoints as Solo Agent dashboard

### 6. Navigation Flows
- **Inbound routes:** `/dashboard` redirect (for team members), sidebar "Dashboard" link
- **Outbound routes:** Same as Solo Agent plus `/admin/task-templates` (Team section), agent drill-down to filtered Active Transactions
- **Deep-link support:** `?view=personal` or `?view=team` query param to persist toggle state

### 7. AI Integration Points
- Same as Solo Agent dashboard but team-scoped
- **Additional AI:** Coach prompts in side rail (AI-generated suggestions for team management actions)
- **AI guardrails:** AI Coach (paid feature) not active in MVP; placeholder only

### 8–10. Same patterns as Solo Agent Dashboard
- Real-time polling for team-scoped data
- First-time team with no transactions → empty state
- Large teams (10+ agents) → agent board paginated or scrollable

---

## 3.4 Attorney Dashboard — `/dashboard/attorney`

**Design reference:** `completed_designs/ve-attorney_dashboard.html`

### 1. Page Identity & Access
- **Route:** `/dashboard/attorney`
- **Page title:** "Attorney Dashboard"
- **Allowed roles:** Attorney
- **Redirect rule:** Non-attorney roles → `/dashboard`
- **Auth requirement:** Protected + Attorney role check

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** Authenticated, onboarding complete, role is Attorney
- **API endpoints consumed on mount:**
  - `GET /api/v1/dashboard/attorney` — aggregated attorney payload:
    - `legal_health_score` (0–100) focused on approval gates
    - `matters_needing_judgment[]` — matters requiring legal decisions
    - `critical_approval_gates[]` — approval actions with deadlines
    - `drift_summary` — { blocked_matters, missing_formal_docs, release_ready_packets }
    - `filter_counts` — { all, needs_review, missing_docs, ready_to_release, clean_files }
    - `matter_cards[]` — per-matter: name, status pills, review items, key dates, AI-prepared next step
    - `state_rules` — active state rules for the attorney's matters
  - `GET /api/v1/ai/briefing?scope=attorney`
  - `GET /api/v1/transactions/kpi?scope=attorney` — KPI tiles: Hard Stops, Release-Ready Packets, Active Matters, Reviewed Volume
- **Loading state UI:** Skeleton with matter card placeholders
- **Empty state UI:** "No active matters assigned to you" with guidance text
- **Error state UI:** Error banner with retry

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Sidebar state:** "Dashboard" active; KPI tiles: Hard Stops (red), Release-Ready Packets, Active Matters, Reviewed Volume (month). Attorney-specific: no "Team" section.
- **Topbar state:** AI briefing chip (attorney-scoped); "+ Upload Packet" CTA instead of "+ New Transaction"
- **Page header:** "Attorney Dashboard" title | Filter tabs: All, Needs Review, Missing Docs, Ready To Release, Clean Files (each with count)
- **Primary content area:**

  **Upload Intake Card (full width):**
  - Drag/drop zone: "Upload title commitments, settlement statements, affidavits, recording packets"
  - "AI will extract deadlines, compare versions, index exhibits, and flag missing formal documents"
  - CTAs: "Open intake" and "Open release queue"

  **Hero Card (legal health score):**
  - Health score ring (0–100) focused on approval gates
  - Action list: critical approval gates needing decision
  - Drift summary: blocked matters, missing formal docs, release-ready packets
  - Filter buttons: Needs Attorney Judgment, Missing Notarized Docs, Ready to Release, Recording/Disbursement Timing

  **Matter Card Stack:**
  - Each card: matter name (address + client), status pills (Critical / Today / Missing Doc), agent name
  - Expandable drawer per card:
    - Review queue with sign-off checkboxes (human action items)
    - Key dates with status colors (overdue = red, today = amber, future = green)
    - AI-prepared next step with context (clearly labeled as "AI-prepared")
  - Footer actions: View Docs, Audit Trail, Send Packet, Price

  **State Rules Panel (collapsible or modal):**
  - Closing mode display
  - Recording timelines
  - Disbursement timing rules
  - Same-day release checks
  - Recording calendar link
  - Legal/audit quick actions

- **Overlay/modal inventory:**
  - Document upload modal (legal packet intake)
  - State rules modal
  - Send packet confirmation modal
  - AI Chat panel

### 4. User Actions & State Transitions

**Sign-off checkbox (in matter card drawer):**
- Trigger: Check a review item checkbox
- Immediate UI: Checkbox fills, item dims slightly
- API call: `POST /api/v1/attorney/approve` with `{ matter_id, item_id, action: 'approve' }`
- Success: Item marked as approved; matter status pill may update; toast "Approved"
- Failure: Checkbox reverts; error toast
- Side effects: Audit log with before/after state; communication log entry; notification to agent/elf

**"Send Packet" click:**
- Trigger: Click
- Immediate UI: Opens Send Packet confirmation modal showing recipients, documents included, and release conditions
- Requires explicit "Confirm Release" button in modal
- API call: `POST /api/v1/attorney/release-packet` with `{ matter_id, recipients[], document_ids[] }`
- Success: Toast "Packet released"; matter moves to "Clean Files" or "Completed"; communication log entry
- Failure: Error toast; no release
- Side effects: Audit log; notifications to all recipients; communication log

**"Open release queue" CTA:**
- Trigger: Click
- Immediate UI: Filter tabs switch to "Ready To Release" filter

**Filter tab click:**
- Trigger: Click on e.g. "Needs Review"
- Immediate UI: Matter card stack filters to show only matters matching that status; count in tab updates
- API call: `GET /api/v1/dashboard/attorney?filter=needs_review` (or client-side filter if all data loaded)

**Matter card expand:**
- Trigger: Click on matter card
- Immediate UI: Card expands to show drawer (review items, key dates, AI next step)
- API call: `GET /api/v1/transactions/:id/attorney-detail` (if not already loaded)

### 5. Conditional Rendering Logic
- **Role-based visibility:** Only Attorney role sees this page. The sign-off checkboxes and release actions are attorney-exclusive.
- **State-based visibility:**
  - Matter cards show different status pills based on state: Critical (overdue approval gate), Today (gate due today), Missing Doc (required formal document not uploaded)
  - "Send Packet" button only enabled when all sign-off items checked and no "Missing Doc" pills present
  - AI-prepared next step clearly bounded: "AI suggests: [action]" with orange-bordered AI indicator
- **AI guardrails — ABSOLUTE:**
  - AI-prepared items are labeled "AI-Prepared" with distinct visual treatment
  - Sign-off checkboxes are always human-only — no auto-check
  - No AI button for "Determine legal equivalence", "Release packet", or "Approve same-day disbursement"
  - These actions require explicit human interaction with confirmation dialogs
- **Responsive behavior:** Matter card stack goes full-width on mobile; filter tabs become horizontally scrollable

### 6. Navigation Flows
- **Inbound routes:** `/dashboard` redirect, sidebar "Dashboard"
- **Outbound routes:**
  - Matter card "View Docs" → document modal
  - Matter card "Audit Trail" → `/transactions/:id?tab=history` (attorney-scoped view)
  - Recording calendar link → `/attorney/recording-calendar`
  - State rules modal opens inline
  - Filter buttons → same page with filter applied

### 7. AI Integration Points
- **AI data on page:** Legal health score, AI-prepared next steps per matter, AI-extracted deadlines and exhibit indexing, version comparisons
- **AI actions available:** AI can compare settlement statement versions, extract deadlines, index exhibits, summarize communication history, draft transmittal/request language
- **AI confidence display:** AI-prepared items show confidence indicator; items below review threshold flagged with "Needs human review" badge
- **AI guardrails (ABSOLUTE — per requirements 8.6):**
  - AI must NOT determine legal equivalence
  - AI must NOT determine legal position
  - AI must NOT approve final packet release
  - AI must NOT approve same-day disbursement exceptions
  - These remain human-owned decisions with mandatory confirmation dialogs
  - If AI confidence is below threshold or a formal/notarized document is missing or legal judgment is required → task stays human-owned with no AI shortcut
- **AI chat panel:** Available — receives attorney's matter list as context; cannot execute release actions

### 8. Real-Time & Notification Behavior
- **Live updates:** Matter card status updates on task completion by others (polling or realtime)
- **Notification triggers:** Attorney sign-off generates notifications to agent/elf; packet release notifies all recipients
- **Toast/alert patterns:** Approval success, release success, upload success; error toasts for failures

### 9. Cross-Page Relationships
- **Shared state:** Filter selection persists in URL query params
- **Dashboard deep-linking:** Filter buttons and matter cards link to filtered views within this page; "View Docs" opens modal overlay
- **Data dependencies:** Matters are transactions with `closing_mode = 'attorney'` assigned to this attorney

### 10. Edge Cases
- **No matters assigned:** Empty state "No active matters" with guidance
- **All matters clean:** High health score; "All matters are current" message
- **Concurrent attorney review:** If two attorneys review the same matter, sign-off checkboxes show real-time state via optimistic updates with conflict detection (last-write-wins with toast notification)
- **State rules vary by transaction:** State rules panel shows rules for the currently expanded matter; changes when expanding a different matter in a different state

---

## 3.5 Administrator Dashboard — `/dashboard/admin`

### 1. Page Identity & Access
- **Route:** `/dashboard/admin`
- **Page title:** "Administrator Dashboard"
- **Allowed roles:** Admin
- **Redirect rule:** Non-admin → `/dashboard`
- **Auth requirement:** Protected + Admin role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/dashboard/admin` — system-wide metrics:
    - `total_users`, `active_users`, `users_by_role`
    - `total_transactions`, `transactions_by_status`
    - `ai_action_summary` (actions this week, approval rate, provider usage)
    - `task_template_stats` (tasks added/removed globally)
    - `recent_audit_logs[]` (last 20 system-wide audit entries)
  - `GET /api/v1/ai/briefing?scope=system`
- **Loading state UI:** Dashboard skeleton with stat card placeholders
- **Empty state UI:** Unlikely (admin always has system data); if fresh tenant → "Welcome! Start by inviting your first agent." CTA
- **Error state UI:** Error banner with retry

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Sidebar state:** "Dashboard" active; KPI tiles: Total Users, Active Transactions, AI Actions (week), Pending Invitations
- **Topbar state:** No "+ New Transaction" CTA; replaced with "+ Invite User"
- **Page header:** "Administrator Dashboard" title
- **Primary content area:**
  - System health overview cards: users by role (bar chart), transactions by status (donut), AI provider usage (pie)
  - AI confidence threshold summary card with link to `/admin/confidence`
  - Recent audit log preview (last 20 entries) with "View All" link to `/admin/audit-logs`
  - Task template statistics: most added/removed tasks, global completion rates
  - Quick action tiles: Manage Users, Task Templates, AI Settings, Tenant Settings, Audit Logs
- **Overlay/modal inventory:** Invite User modal

### 4. User Actions & State Transitions
- **Quick action tile clicks:** Navigate to respective admin pages
- **"+ Invite User" CTA:** Opens Invite User modal → enter email, select role, optional team → sends invitation email
- **Audit log row click:** Navigate to `/admin/audit-logs?id=:logId`
- **AI provider toggle:** Navigate to `/admin/tenant` settings page

### 5. Conditional Rendering Logic
- **Role-based:** Admin-only page; all elements visible to Admin
- **State-based:** If tenant has no AI provider configured → prominent warning card "AI features require provider configuration" with link to settings

### 6–10. Standard patterns
- Inbound from `/dashboard` redirect; outbound to admin sub-pages
- Real-time: audit log updates via polling (30 second)
- Edge cases: first admin setup → wizard-like guidance cards

---

# 4. Deals Section

---

## 4.1 Active Transactions — `/transactions/active`

**Design reference:** `completed_designs/ve-active_transactions.html`

### 1. Page Identity & Access
- **Route:** `/transactions/active`
- **Page title:** "Active Transactions"
- **Allowed roles:** Agent, Elf, Team Lead, Attorney, Admin
- **Redirect rule:** Client → `/client/transactions`; FSBO → `/fsbo`; Vendor → 403
- **Auth requirement:** Protected + internal role check

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** Authenticated, onboarding complete, internal role
- **API endpoints consumed on mount:**
  - `GET /api/v1/transactions?status=Active&page=1&limit=20` with optional query params:
    - `filter` — all|overdue|due_today|closing_soon|in_inspection|on_track|unhealthy
    - `sort` — urgency (default)|close_date|client_name|price
    - `search` — text search across client names, vendor names, companies, dates, addresses
    - `agent` — filter by agent ID (team view)
    - `highlight` — transaction ID to auto-scroll and expand
  - `GET /api/v1/ai/briefing` — topbar briefing counts
  - `GET /api/v1/transactions/kpi` — sidebar KPI tiles
  - `GET /api/v1/transactions/tab-counts` — counts for each filter tab
- **Loading state UI:** Page header with tab bar (counts show "–" placeholder); content area shows 3–5 transaction card skeletons with pulsing placeholders for status pill, name, address, milestone bar, and info badges
- **Empty state UI:** "No active transactions" centered illustration with: "Get started by creating your first transaction" text and prominent "+ New Transaction" button. If a specific filter is selected with no results: "No transactions match '[filter name]'" with "Clear filter" link.
- **Error state UI:** Error banner "Unable to load transactions" with Retry button; if partial data loaded, show stale data with warning badge

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Sidebar state:** "Active Transactions" nav link active (highlighted with orange indicator). KPI tiles: Overdue Tasks (count, red if > 0), Closing This Week (count), Active Deals (count), Pipeline Value (currency). Deals section counts: Active Transactions (badge), Pending (badge), Closed, All Transactions.
- **Topbar state:** AI briefing chip with Critical/Needs Attention/On Track counts (each clickable to set filter). Global search input. Notification bell. User chip. "+ New Transaction" CTA button.
- **Page header:**
  - Breadcrumb: Deals > Active Transactions
  - "Active Transactions" title + count pill (total matching current filter, mono font)
  - Action buttons: "Export CSV" | "Print Report"
  - Tab bar: All (count) | Overdue (count, red text if > 0) | Due Today (count, amber) | Closing Soon (count) | In Inspection (count) | On Track (count, green) | Unhealthy (count, red)
  - Below tabs: Sort control dropdown (Urgency | Close Date | Client Name | Price) + inline search input
- **Primary content area — Transaction Card List:**

  Each transaction renders as a collapsible card:

  **Card Collapsed State:**
  - Left edge: Vertical color bar indicating urgency (red = critical, amber = warning, green = on track)
  - Row 1: Client name (bold) | Property address | Status pill (Critical / Needs Attention / On Track / In Inspection / Unhealthy) + "why" badges (e.g., "2 overdue", "no client touch 5 days", "missing inspection response")
  - Row 2: AI next-step banner (champagne glow background, orange left border): icon + "Next step: [action description]" + context sub-text + CTA button (e.g., "Send Response", "Request Docs")
  - Row 3: Primary contact (name, role) with clickable `tel:` phone link and `mailto:` email link (stopPropagation to avoid card toggle) | Milestone bar: Contract → EM → Inspection → Appraisal → CD Delivered → CTC → Close (filled steps = green, current = amber, future = gray, overdue = red)
  - Row 4: Info badges: Tasks (overdue/total) | Emails | Notes | Missing Docs | Client Touch (days) | Lender Touch (days) | History count
  - Right summary block: Days to Close (mono, large) | Overdue count or "No Overdue" (green/red) | Purchase Price (mono)
  - Expand chevron (right side)

  **Card Expanded State (Drawer):**
  Three-column layout:

  **Column 1 — Tasks:**
  - Section title: "Tasks" with "+ Add" link
  - Grouped: Overdue (red header, overdue task items) | Upcoming (task items with due dates) | Completed (dimmed, collapsed by default)
  - Each task row: checkbox (click to complete) | task name | due date (mono, red if overdue) | assigned-to avatar
  - "+ Add Task" button at bottom → opens Add Task modal

  **Column 2 — Key Dates:**
  - Section title: "Key Dates" with "(click to edit)" hint
  - Date rows, each with:
    - Label (e.g., "EM Delivered", "Inspection Response", "Closing Date")
    - Date value (mono font, red if overdue, amber if today, green if future)
    - Pencil edit icon → click opens inline date popover
    - For Closing Date and Possession: also shows time-of-day or "Time: TBD"
  - Full list: EM Delivered | Inspection Response | Appraisal Expected | CD Delivered | Cleared to Close | Closing Date (+ time) | Possession (+ time)

  **Column 3 — Contacts:**
  - Section title: "Contacts"
  - Grouped by role: Buyer | Seller | Listing Agent | Buyer's Agent | Lender | Title | Inspector | etc.
  - Each contact: name | company | one-click phone icon | one-click email icon
  - Expand/collapse per group
  - Empty slots show "Add [role]" link (e.g., "Add title company") → opens Add Contact modal
  - Secondary contact support: "Add contact" link under existing primary

  **Below columns:**
  - AI Suggestions panel: "AI Suggestions for This Deal" with up to 3 contextual suggestions computed client-side from card state: overdue task review, draft inspection response (if date missing), prepare closing checklist (if close ≤14 days), upload documents (if doc_count=0), AI next-step help. Each suggestion button opens AI Chat panel. Panel only renders when ≥1 suggestion applies.
  - Footer actions bar: "View/Add Documents" | "Print Checklist" | "Transaction History" | Price display

- **Overlay/modal inventory:**
  - New Transaction quick-create modal
  - Add Task modal
  - Add Contact modal
  - Transaction Documents modal
  - All Documents search modal (sidebar link)
  - Transaction History side panel
  - Edit Date popover (inline)
  - AI Chat floating panel
  - Print Checklist (browser print)
  - Export CSV download

### 4. User Actions & State Transitions

**Tab click (e.g., "Overdue"):**
- Trigger: Click tab
- Immediate UI: Active tab highlighted; card list filters to show only matching transactions; URL updates to `?filter=overdue`; count pill updates
- API call: `GET /api/v1/transactions?status=Active&filter=overdue` (or client-side filter if all loaded)
- Success: Card list updates
- Failure: Toast; revert to previous tab

**Sort control change:**
- Trigger: Select new sort option
- Immediate UI: Card list reorders; URL updates to `?sort=close_date`
- API call: Client-side sort if all data loaded; otherwise `GET /api/v1/transactions?sort=close_date`

**Search input:**
- Trigger: Type in search field (debounced 300ms)
- Immediate UI: Card list filters in real-time; matching text highlighted in cards
- API call: `GET /api/v1/transactions?search=:query` (if server-side) or client-side filter
- Success: Filtered results; "X results" count shown
- Empty results: "No transactions match '[query]'" with clear button

**Transaction card click (expand/collapse):**
- Trigger: Click on card (not on interactive elements within card)
- Immediate UI: Card expands with slide-down animation showing 3-column drawer (tasks, key dates, contacts)
- Data source: All drawer data (task sections, key dates, contact groups, AI suggestions) is included in the `GET /api/v1/dashboard/transaction-cards` response — no separate detail fetch needed
- AI suggestions panel: Populated client-side from card state (overdue task count, missing key dates, approaching close date, document count)

**AI next-step banner (`tab-banner-sub` text):**
- **Data source:** `TransactionCardAPI.ai_next_step` returned by `GET /api/v1/dashboard/transaction-cards`. Each card also reports `ai_next_step_source: 'ai' | 'rule'` and `ai_next_step_updated_at`. Both fields exist only for internal frontend logic and are not displayed — the banner looks identical in both modes so users never see an "AI vs rule" distinction.
- **Cache strategy:** Backend caches the AI-generated sentence in `transactions.ai_next_step_text` / `_cta` / `_updated_at`. On dashboard load, the endpoint serves the cached text if it's non-null and less than 24 hours old (`ai_next_step_cache.is_fresh`) → `source: 'ai'`. Otherwise it returns the rule-based fallback from `_derive_ai_next_step` (inline, instant) → `source: 'rule'`, AND schedules a background `BackgroundTasks` job (`_background_refresh_ai_next_steps`) that regenerates the real AI text via `AIService.generate_next_step_guidance` with bounded concurrency (`REFRESH_CONCURRENCY = 4`).
- **Silent frontend auto-refresh:** `TransactionListPage` watches `cardsResponse.items`. Whenever any card has `source === 'rule'` and its transaction ID hasn't been refreshed in this session yet, the page waits 3 seconds (time for the LLM call to complete) and calls `queryClient.invalidateQueries({ queryKey: ['dashboard', 'transaction-cards'] })`. The subsequent refetch picks up the freshly-cached AI text and the banner content updates in place. A session-scoped `pendingAiRefreshRef` Set dedupes so each transaction triggers at most one silent refresh per page lifetime, preventing loops when the LLM provider is unavailable.
- **Cache invalidation (cost minimization):** The cache is cleared only at state-change write sites — any call that can shift the next-deadline task or key inputs:
  - `POST /api/v1/tasks` (new task may become next deadline)
  - `PATCH /api/v1/tasks/:id` when `name`, `status`, or `due_date` changes
  - `PUT /api/v1/tasks/:id/status` (always)
  - `DELETE /api/v1/tasks/:id` (always)
  - `PATCH /api/v1/transactions/:id` when `closing_date`, `address`, or `use_case` changes
  - `PUT /api/v1/transactions/:id/key-dates` (always — any key date shifts the timeline)
  All invalidations route through `ai_next_step_cache.invalidate()` which nulls the three DB columns. No state change = no invalidation = 0 LLM calls. Each real state change produces exactly **one** LLM call on the next dashboard fetch, which is then cached for 24 hours.
- **Graceful failure:** If the LLM provider is unavailable, `refresh_one` logs a warning and leaves the cache untouched. The next dashboard fetch still serves the rule-based fallback so the banner is never empty. The retry only happens on the next state change (not on every page load), avoiding runaway costs during provider outages.

**AI next-step CTA button click (e.g., "Send Response"):**
- Trigger: Click
- Immediate UI: Opens AI Chat side panel
- Current state: Chat panel uses `POST /api/v1/dashboard/ai-chat` which returns placeholder responses. Full AI action engine (draft generation, contextual responses) deferred to Phase 3 (Milestone 3.1+)
- Future: Pre-filled action context with `POST /api/v1/ai/action` for contextual draft generation

**Task checkbox click (complete task):**
- Trigger: Click checkbox in expanded task list (only non-completed tasks are clickable)
- API call: `PATCH /api/v1/tasks/:id` with `{ status: 'Completed' }` — backend automatically sets `completed_at`
- Success: Dashboard query cache invalidated → card refreshes with updated task sections, counts, and stage pill; toast "Task completed"
- Failure: Error toast "Failed to complete task"
- Side effects: Backend writes audit log; task-dependent tasks may become unblocked

**"+ Add Task" click:**
- Trigger: Click "+ Add" header link or "+ Add Task" dashed button in expanded tasks column
- Immediate UI: Opens Add Task modal with transaction context (deal name badge, transactionId passed through)
- Modal fields: Task Name (required), Completion Method (phone_call | email | e_signature | in_person | upload_document | online_portal | ai_agent | other), Due Date, Assign To (Myself | AI Agent)
- "Get AI Suggestions on How to Complete" button → `POST /api/v1/ai/suggest-task-approach` with `{ task_name, completion_method?, transaction_id? }`; returns `{ approaches: [{ description, suggested_method, rationale }] }`. MVP uses a keyword-based rule engine on the backend (inspection/appraisal, signing/contract, upload/document, call/follow-up, title/escrow/loan — falls back to a generic trio). Panel renders inline below the form with a loading spinner during the fetch; each approach is a clickable card. Clicking a card auto-fills the Completion Method dropdown with the suggested method and shows a toast confirming the selection. Panel includes Regenerate and Hide buttons. Phase 3 will upgrade the backend path to a live chat-completion provider call while preserving the same request/response contract.
- On submit: `POST /api/v1/tasks` with `{ name, transaction_id, completion_method?, due_date?, assigned_to? }`
- Success: Dashboard cache invalidated → card refreshes; modal clears and closes; toast "Task added"
- Failure: Error toast with API message; modal stays open
- Loading state: Submit button shows spinner and is disabled during request
- Future: AI similar-task dedup check before saving (Phase 3)

**Key date row click (edit):**
- Trigger: Click anywhere on a key date row (row highlights on hover with "(click to edit)" hint in section header)
- Immediate UI: `DateEditPopover` appears anchored near the clicked row with date picker, Save and Cancel buttons
- Save click: Optimistic local display update (formatted date, green color) + API call `PUT /api/v1/transactions/:id/key-dates` with `{ [field_name]: 'YYYY-MM-DD' }` where field_name comes from the backend's `KeyDateAPI.field_name` (e.g., `em_delivered_date`, `inspection_response_date`, `closing_date`)
- Success: Dashboard cache invalidated → card refreshes; toast "Date updated"
- Failure: Error toast "Failed to update date" (local optimistic display remains until cache refresh corrects it)
- Cancel click: Popover closes, no changes
- Side effects: Backend writes audit log with before/after state

**Contact phone icon click:**
- Trigger: Click phone icon
- Immediate UI: Initiates `tel:` link (opens phone dialer on mobile, may open calling app on desktop)
- Future: Click-to-call/call-bridge integration

**Contact email icon click:**
- Trigger: Click email icon
- Immediate UI: Opens email compose (either in-app compose if email connected, or `mailto:` fallback)

**"Add [role]" contact link click / contact "+" button click:**
- Trigger: Click dashed "Add [role]" placeholder (empty group) or the "+" button on an existing contact row
- Immediate UI: Opens Add Contact modal with role label pre-set and transactionId passed through
- Fields: Company Name (shown for Lender/Title roles), First Name (required), Last Name, Phone Number, Email Address
- Submit: `POST /api/v1/transactions/:id/parties` with `{ party_role, full_name, email?, phone?, company? }` — role label mapped to API role (e.g., "Lender" → "loan_officer", "Title" → "title_rep")
- Success: Dashboard cache invalidated → contacts column refreshes; modal clears and closes; toast "Contact added"
- Failure: Error toast with API message; modal stays open
- Loading state: Submit button shows spinner and is disabled during request

**"View/Add Documents" footer click:**
- Trigger: Click
- Immediate UI: Opens Transaction Documents modal
- Shows document list for this transaction with status indicators
- Actions: Upload new, rename, view/download, email, send for e-signature, view version history

**"Print Checklist" footer click:**
- Trigger: Click
- Immediate UI: Generates closing checklist from user's profile templates
- API call: `GET /api/v1/transactions/:id/checklist` → returns Buyer or Seller template (based on transaction use case) populated with transaction data, tagged notes from profile, seller escrow overage reminders
- Success: Browser print dialog opens
- Failure: Toast "Unable to generate checklist. Check your profile templates."

**"Transaction History" footer click:**
- Trigger: Click
- Immediate UI: Opens Transaction History side panel (slides in from right)
- Shows searchable event timeline grouped by date headings (Today, Yesterday, [Date])
- Events: AI flags, emails received, task completions, date confirmations, offer events, document actions
- Search input at top filters events by keyword
- API call: `GET /api/v1/transactions/:id/history`

**"Export CSV" button click:**
- Trigger: Click
- Immediate UI: Button shows spinner
- API call: `GET /api/v1/transactions/export?format=csv&filter=:currentFilter`
- Success: CSV file downloads; toast "Export complete"
- Failure: Toast "Export failed"

**"+ New Transaction" CTA click:**
- Trigger: Click (topbar or sidebar)
- Immediate UI: Opens New Transaction quick-create modal
- See Cross-Cutting Workflow A for complete specification

### 5. Conditional Rendering Logic
- **Role-based visibility:**
  - **Agent:** Sees own transactions only; can create, edit, complete tasks, edit dates
  - **Elf:** Sees assigned transactions; same actions as Agent except cannot change master templates
  - **Team Lead:** Sees all team transactions; additional "Team member" filter dropdown in page header; assignee name shown on each card; can access Task Templates from sidebar
  - **Attorney:** Sees transactions with `closing_mode = 'attorney'` assigned to them; sign-off checkboxes appear in expanded drawer; legal-specific "why" badges (e.g., "missing notarized doc"); AI next-step items clearly marked "AI-Prepared"
  - **Admin:** Can see all transactions (read access); limited action capabilities (observe, not modify transactions directly)
- **State-based visibility:**
  - "In Inspection" tab only shows count > 0 when transactions have unsent inspection responses
  - "Why" badges compute from: overdue tasks, missing documents, stale communication (no client/lender touch), approaching deadline with blockers
  - Stage pills computed from transaction state + task status + dates + message counts + missing docs
  - AI next-step banner: shown whenever the transaction has an active deadline task; text is AI-generated (cached 24h) with a keyword rule-based fallback on cold cache or LLM failure
  - Empty contact slots: show "Add [role]" placeholder
  - Time-of-day fields on Closing Date and Possession: show "Time: TBD" until set
- **Feature flags:** None on this page
- **Responsive behavior:**
  - Desktop (≥1280px): Full layout with sidebar, transaction cards with all columns in drawer
  - Tablet (768–1279px): Sidebar collapses to icons; drawer becomes 2-column (tasks/dates stacked, contacts below)
  - Mobile (<768px): Sidebar hidden (hamburger menu); cards simplified (milestone bar hidden); drawer becomes single column stack; tabs horizontally scrollable

### 6. Navigation Flows
- **Inbound routes:**
  - Sidebar "Active Transactions" link
  - Dashboard fast filters (e.g., `/transactions/active?filter=critical`)
  - Dashboard action queue items (e.g., `/transactions/active?highlight=:id`)
  - AI briefing chip clicks
  - Global search results
  - Direct URL entry
- **Outbound routes:**
  - Transaction card expanded footer "View/Add Documents" → Transaction Documents modal (overlay, stays on page)
  - "Print Checklist" → browser print dialog
  - "Transaction History" → side panel (overlay)
  - Sidebar links → respective pages
  - AI next-step CTA → AI Chat panel (overlay)
  - Card click on transaction name/address → `/transactions/:id` (full transaction detail page)
- **Deep-link support:**
  - `?filter=overdue` — sets active tab
  - `?sort=close_date` — sets sort
  - `?search=smith` — sets search
  - `?agent=:id` — filters by agent (team view)
  - `?highlight=:id` — auto-scrolls to and expands specific transaction card
  - All query params are independently combinable
- **Back navigation:** Browser back restores previous filter/sort/search state (encoded in URL)

### 7. AI Integration Points
- **AI data on page:**
  - Topbar AI briefing counts (Critical, Needs Attention, On Track)
  - Stage pills (AI-computed from transaction health signals)
  - "Why" badges (AI-analyzed risk factors)
  - AI next-step banners per card (AI-recommended action with context)
  - AI Suggestions panel in expanded drawer
- **AI actions available:**
  - AI next-step CTA buttons (draft responses, request docs, etc.)
  - AI chat panel with transaction context when card is expanded
  - AI similar-task check when adding tasks
  - AI document intake when dropping files
- **AI confidence display:**
  - AI next-step items show confidence implicitly (items below review threshold have "Needs review" badge instead of action CTA)
  - AI suggestions in drawer show confidence level per suggestion
- **AI guardrails:**
  - AI cannot auto-complete tasks, auto-change dates, or auto-send communications from this page
  - AI recommendations require user click/confirmation
  - Attorney-specific: AI-prepared items clearly labeled; legal judgment items have no AI shortcut
- **AI chat panel:** Available. When a transaction card is expanded, chat receives that transaction's context. Quick-action prompts: "Show overdue tasks", "Draft inspection response", "Summarize [client] deal"

### 8. Real-Time & Notification Behavior
- **Live updates:**
  - Transaction card data refreshes via polling (60s) or Supabase Realtime
  - If another user completes a task → task list updates, info badges update, stage pill recalculates
  - New document uploads → info badge updates
  - Tab counts refresh on data change
- **Notification triggers:**
  - Task completion → notification to transaction participants
  - Date change → notification to assigned agent/elf
  - Document upload → notification to transaction owner
- **Toast/alert patterns:**
  - Task complete: success toast "Task completed"
  - Date changed: success toast "Date updated" (+ "3 task deadlines adjusted" if cascading)
  - Contact added: success toast
  - Export complete: success toast
  - Errors: error toasts with specific messages

### 9. Cross-Page Relationships
- **Shared state:** Current filter, sort, and search selections persist in URL; workspace view (personal vs. team) for Team Leads persists via localStorage or URL
- **Dashboard deep-linking:** All dashboard cards, fast filters, and AI prompts open filtered views of this page
- **Data dependencies:** This page is the primary transaction workspace. Dashboard cards link here. Task Queue links to individual tasks shown here. All Documents links to documents across transactions shown here.

### 10. Edge Cases
- **First-time user:** After creating first transaction from empty state, page shows the new transaction card. If profile setup incomplete, banner: "Complete your profile for full functionality" with link.
- **Transaction type switching:** If a transaction's use case changes (e.g., Financing → Cash), the card refreshes with updated tasks (completed tasks preserved, new tasks added, inapplicable tasks removed/sleeping). Toast: "Transaction type updated. X tasks adjusted."
- **Concurrent editing:** If two users edit the same transaction's dates simultaneously, last-write-wins with toast notification to the user whose change was overridden: "This date was just updated by [other user]"
- **Offline/slow network:** Optimistic updates for task completion with retry queue. If offline, show "You're offline" banner; queue actions for sync when reconnected.
- **Large data sets (100+ transactions):** Pagination with "Load more" button (20 per page). Virtual scrolling for smooth performance. Tab counts always reflect total regardless of page.
- **Document drag-and-drop:** Dropping a document anywhere on the page (not just on a card) triggers the global document intake flow: AI identifies document → suggests name → asks which transaction → checks signature needs. See Cross-Cutting Workflow D.
- **Print report:** Generates PDF summary of all visible transactions (respecting current filter)

---

## 4.2 Pending Transactions — `/transactions/pending`

### 1. Page Identity & Access
- **Route:** `/transactions/pending`
- **Page title:** "Pending Transactions"
- **Allowed roles:** Agent, Elf, Team Lead, Attorney, Admin
- **Redirect rule:** External roles → their portals
- **Auth requirement:** Protected + internal role

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** Authenticated, internal role
- **API endpoints on mount:**
  - `GET /api/v1/transactions?status=Active` — same endpoint as Active Transactions (pending = active non-closed transactions; this is functionally equivalent to Active Transactions as per requirements: "Pending — all active transactions that aren't closed")
  - Same KPI and briefing endpoints
- **Loading/Empty/Error states:** Same patterns as Active Transactions

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Sidebar state:** "Pending" nav link active
- **Page header breadcrumb:** Deals > Pending
- **Identical to Active Transactions workspace** — this route serves as a named alias. The sidebar "Pending" link navigates here, and the page renders the same workspace with the same data (active, non-closed transactions). This preserves a future hook for differentiating "Active" (listings) from "Pending" (under contract) in v2.
- **All components, overlays, actions, and behaviors:** Same as `/transactions/active`

### 4–10. Same as Active Transactions
- All actions, conditional rendering, navigation, AI integration, real-time behavior, and edge cases are identical
- **Note for v2:** This route will be differentiated when "Active Listings" functionality is built. For MVP, Pending = Active Transactions.

---

## 4.3 Closed Transactions — `/transactions/closed`

### 1. Page Identity & Access
- **Route:** `/transactions/closed`
- **Page title:** "Closed Transactions"
- **Allowed roles:** Agent, Elf, Team Lead, Attorney, Admin
- **Redirect rule:** External roles → their portals
- **Auth requirement:** Protected + internal role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/transactions?status=Closed&page=1&limit=20&sort=closing_date_desc`
  - Same KPI and briefing endpoints (though KPI tiles reflect global counts, not just closed)
- **Loading state UI:** Transaction card skeletons
- **Empty state UI:** "No closed transactions yet" with subtle illustration
- **Error state UI:** Error banner with retry

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Sidebar state:** "Closed" nav link active
- **Page header:** Breadcrumb: Deals > Closed | "Closed Transactions" title + count pill | "Export CSV" action
- **Tab bar:** None (closed transactions do not need status filter tabs)
- **Sort options:** Close Date (default, newest first) | Client Name | Price
- **Transaction cards:** Same card pattern as Active Transactions but:
  - No status pill urgency (all show "Closed" in neutral gray)
  - No AI next-step banner
  - No "why" badges
  - Milestone bar shows all steps completed (all green)
  - Collapsed footer: "View Documents" | "Print Checklist" | "Transaction History"
- **Expanded drawer:** Same 3-column layout but:
  - Tasks: all shown as completed (read-only, no checkboxes)
  - Key dates: all set (read-only, no edit icons)
  - Contacts: read-only display

### 4. User Actions & State Transitions
- **Card expand:** Same as Active Transactions (read-only)
- **"View Documents":** Opens Transaction Documents modal (read-only)
- **"Print Checklist":** Same as Active Transactions
- **"Transaction History":** Same as Active Transactions
- **"Export CSV":** Same as Active Transactions
- **No task editing, date editing, or contact adding** on closed transactions

### 5. Conditional Rendering Logic
- **Role-based:** Same role-based transaction visibility rules
- **State-based:** All interactive editing elements hidden/disabled for closed transactions
- **Post-closing feedback prompt:** If a transaction was recently closed (within 7 days) and the user has not provided feedback → a subtle banner at the top of the expanded card: "How was this transaction? Quick feedback helps AI improve." with link to feedback modal (useful / unnecessary / missing tasks)

### 6–10. Standard patterns
- Navigation: Inbound from sidebar "Closed"; outbound to document modals, print, history
- No AI next-step actions on closed transactions
- Edge cases: Post-closing reminders (tax exemptions, reviews) may appear as toast notifications when viewing recently closed transactions

---

## 4.4 All Transactions — `/transactions/all`

### 1. Page Identity & Access
- **Route:** `/transactions/all`
- **Page title:** "All Transactions"
- **Allowed roles:** Agent, Elf, Team Lead, Attorney, Admin
- **Auth requirement:** Protected + internal role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/transactions?page=1&limit=20` — all transactions regardless of status
  - Optional filters: `status` (Active, Incomplete, Paused, Completed, Closed), `sort`, `search`
- **Loading/Empty/Error:** Same patterns

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Sidebar state:** "All Transactions" nav link active
- **Page header:** Breadcrumb: Deals > All Transactions | "All Transactions" title + count pill | "Export CSV"
- **Tab bar:** All | Active | Incomplete | Paused | Completed | Closed (each with count)
- **Sort options:** Urgency | Close Date | Client Name | Price | Status
- **Transaction cards:** Same pattern; status pill reflects actual status (Active, Incomplete, Paused, Completed, Closed) with appropriate colors
- **Expanded drawer:** Same layout; edit capabilities depend on transaction status (Active/Incomplete/Paused = editable; Completed/Closed = read-only)

### 4–10. Combines behaviors of Active and Closed pages based on per-transaction status
- Active/Incomplete/Paused transactions: full edit capabilities
- Completed/Closed transactions: read-only
- Additional status filter tab bar differentiates from Active Transactions page

---

## 4.5 New Transaction — `/transactions/new`

### 1. Page Identity & Access
- **Route:** `/transactions/new`
- **Page title:** "New Transaction"
- **Allowed roles:** Agent, Elf, Team Lead
- **Redirect rule:** Non-authorized roles → `/dashboard` with toast
- **Auth requirement:** Protected + creation-capable role

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** User can create transactions; the full wizard flow is used for document-first creation
- **API endpoints on mount:**
  - `GET /api/v1/users/me` — pre-fill agent info
  - `GET /api/v1/contacts?is_preferred=true` — preferred vendors for auto-suggest
- **Loading state UI:** Wizard skeleton
- **Error state UI:** Error toast + retry

### 3. Layout & Component Hierarchy
- **Shell variant:** Standalone wizard (minimal shell — logo + top stepper, no sidebar)
- **Primary content area:** Multi-step wizard — see Cross-Cutting Workflow A for complete specification
- **Phases (public 4-phase stepper; internal steps in parentheses) — four-step
  reorganization + Jake's answers, 2026-07:**
  1. Upload (Document Upload → AI Parsing Progress)
  2. Contract Details (`purchase`) — property address + price/dates/financing/
     contingencies/notes on one step; a "✦ Found in the contract — needs your
     eyes" band surfaces no-default decisions (who orders title, cash-deal
     appraisal election)
  3. Contacts & Fees (`address`) — parties (each a full contact card) + the two
     fee cards (Professional + Transaction). A fee is paid by Buyer / Seller /
     Both; each paying side carries its OWN amount and `%`/`$` unit (so "Both"
     is two independent rows, e.g. seller 2% + buyer $250). A contract-stated
     fee shows as a read-only hint; the cards prefill from the last deal
     (localStorage) and are withheld from create until confirmed or edited.
     `missing` (Missing Info) is a hidden auto-skip grouped in this phase.
  4. Verification (`confirm`) — the review summary (source-linked value tables),
     the folded Timeline anchor + AI proposal cards (deadlines, compliance,
     tasks), the deal brief, the signature decision (client → e-sign queue;
     counterparty → "request the signed copy from the other agent" task), and
     referenced-missing-doc requests. **Create happens here** via a full-width
     **"Upload Transaction"** button + disclaimer; the footer is Back-only.
     Tasks/timeline/compliance are generated + auto-matched at commit.
- **Retired from navigation (kept as legal step ids for stale-draft coercion):**
  the standalone `timeline`, the manual attach-documents `checklist`, and the
  `review` (Tasks preview) steps. The compliance-checklist EDIT surface moved to
  the transaction workspace; requirements still auto-match + commit at create.

### 4. User Actions & State Transitions
- See Cross-Cutting Workflow A for complete action specification per step

### 5. Conditional Rendering Logic
- Wizard steps adapt based on:
  - Documents uploaded vs. manual entry (if no documents → skip AI parsing, go to manual forms)
  - Transaction type detected → shows relevant fields
  - Closing mode detection → shows attorney/title fields if applicable
- FSBO transactions: property-centric pre-contract state supported

### 6. Navigation Flows
- **Inbound:** "+ New Transaction" CTA (from anywhere), quick-create modal "Full Wizard" link, sidebar CTA
- **Outbound:** After confirmation → `/transactions/active` (or `/transactions/:id` for the new transaction)
- **Back navigation:** Back button between steps; "Save as Draft" option for Incomplete status

### 7. AI Integration Points
- Core AI functionality: document parsing, data extraction, address validation, missing info search
- Double-check mechanism: two-pass extraction with agreement check
- Confidence scoring per field
- See Cross-Cutting Workflow A for full AI specification

### 8–10. Standard patterns
- Edge cases: blurry docs, missing pages, partial extraction → fallback to manual entry with toast
- Browser refresh: draft state preserved per session

---

## 4.6 Transaction Detail — `/transactions/:id`

### 1. Page Identity & Access
- **Route:** `/transactions/:id`
- **Page title:** "[Client Name] — [Address]"
- **Allowed roles:** All roles with access to this transaction (based on assignment, role, and tenant)
- **Redirect rule:** If user has no access to this transaction → 403 page. If transaction doesn't exist → 404 page.
- **Auth requirement:** Protected + transaction access check

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** Transaction exists, user has access
- **API endpoints on mount:**
  - `GET /api/v1/transactions/:id` — full transaction data
  - `GET /api/v1/transactions/:id/tasks` — all tasks
  - `GET /api/v1/transactions/:id/documents` — all documents
  - `GET /api/v1/transactions/:id/parties` — all parties/contacts
  - `GET /api/v1/transactions/:id/communications` — communication log
  - `GET /api/v1/transactions/:id/history` — audit/event timeline
- **Loading state UI:** Tabbed page skeleton with header placeholder
- **Error state UI:** 404 "Transaction not found" or 403 "You don't have access"

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell (Attorney keeps the Matter Workspace on the same route)
- **Sidebar state:** DEALS group, "Transactions" highlighted
- **Page header (sticky white bar; the page owns its scroll):**
  - Breadcrumb: Deals › Transactions › [street address]
  - Serif identity row: client names + stage pill + inline address
  - Status pill dropdown (status change with confirm; Closed asks for post-closing feedback)
  - Champagne "AI next step" strip (from the plan aggregate)
  - Tab pills (active = bg-ve-orange) + quick-action pills: Add Task | Upload Document (classified-upload dialog) | Sync Deadlines | More ▾ (Compose, Print closing checklist, Ask the AI)
- **Creation receipt strip (first visit after the wizard only, `?created=1`):** one flat green line — "Created just now · N tasks (M handled by AI) · N checklist items · N documents attached · Fees captured · E-signature queued · N requests to the other agent" — each segment linking to the tab whose rows back that number, dismissible, never shown again. Segments render only when their count is real.
- **No overview/KPI/tracking/brief band above the tabs.** The body is the agent pane (persistent left column on xl) beside the workbench, and the workbench is its own tab bar plus the active tab. The deal brief lives INSIDE the Timeline tab (below).
- **Tab bar:** Timeline | Compliance | Documents | Tasks | People | Activity (+ Agent on narrow screens)
- **Primary content area (per tab; ONE card per tab):**

  **Timeline Tab:**
  - The plan, alive: core dates, term-derived deadlines, deadline tasks, optional document due dates (pill toggle)
  - Command bar ("Tell me what to change" — closed intents, preview-then-apply, undo)
  - Mini-map; core-date/term edits run the cascade preview → Apply → Undo
  - Add Deadline modal (shared rule editor; server-resolved); remove = Skipped + Undo chip

  **Compliance Tab:**
  - The living checklist: Open / Uploaded / Waived groups with due chips and AI evidence chips
  - Add Document modal (real upload + classification + optional due rule; no-file path is the explicit secondary choice)
  - Per-row actions: Attach Document modal (pick an existing file OR upload right here) | Request by email (drafts into AI Email Review) | Waive + Undo | inline Edit (rule re-resolves server-side)
  - Uploaded rows: "Matched: <file>" + Detach; AI verification chip on every upload (checking → confirmed / "AI read this as X - expected Y" with Use AI type / Keep my type / Detach & re-attach)
  - Empty state: one-click "Generate the standard checklist" or "Add a document"

  **Documents Tab:**
  - Document list (name, type, date, size, version) with download; AI verification chip per row
  - Upload button + header quick action → classified-upload dialog (file + name + type); drag-drop anywhere on the page stays instant-upload; every upload path is AI-verified
  - "Open documents manager" → the full manager modal (rename/classify, versions, email, delete, parse-confirm, missing-documents panel with the same Attach modal)

  **Tasks Tab:**
  - Grouped sections (Overdue / Due Today / Upcoming / Completed) with status menu, basis chips, related-compliance links, Auto-Email toggle (eligible targets only), AI evidence chips
  - Add Task modal (shared Dialog; completion method + assignee via branded selects; AI-suggested approaches)

  **People Tab:**
  - **Deal fees** at the top: the professional fee and transaction fee as "3% · seller" / "buyer $250 · seller 2%" rows, editable in place (pencil → Radix dialog with the wizard's fee-card anatomy: Buyer/Seller/Both, one amount + `%`/`$` per paying side, "Remove fee"); with no fees entered an editing role sees "+ Add fees", and a viewer without edit rights sees nothing at all. Mirrors the `PATCH /transactions/{id}` role gate (Agent / TeamLead / Admin, D5); every edit lands in the Activity audit trail. Fees live here — with the deal's commercial relationships — because the deal brief / overview band stays off the workspace page (Jan's 2026-06-13 review).
  - Representation-aware groups (Buyer, Seller, Agents, Lender, Title + Other contacts); add/edit via AddContactModal; Assign team; Manage client access; client thread; compose

  **Activity Tab:**
  - History feed (audit + task events) with search; Communications panel mounts from page context
  - NOTE: compliance/document audit events do not surface here yet (optional backend item O2 in the refinement plan)

- **Overlay/modal inventory:**
  - Add Document modal (Compliance: add | attach modes; Documents: upload mode) — the canonical upload dialog
  - Add Deadline modal
  - Add Task modal (shared Dialog shell)
  - Add Contact / Assign Team / Manage Client Access modals
  - Compose Email modal; Post-closing feedback modal
  - Documents manager modal (with Missing-documents panel)
  - AI Chat panel; Print Checklist

### 4. User Actions & State Transitions

**"Edit Transaction" button:**
- Trigger: Click
- Immediate UI: Opens edit modal with current transaction fields
- Fields: Address, city, state, zip, purchase price, financing type, closing date, closing mode, use case, notes, all key dates
- Use case change triggers: type switching logic (see Cross-Cutting Workflow B)
- Save: `PATCH /api/v1/transactions/:id`
- Success: Transaction data updates; if use case changed → tasks regenerated with preservation logic; toast "Transaction updated"
- Side effects: Audit log; task recalculation if dates/type changed

**Tab switching:**
- Trigger: Click tab
- Immediate UI: Content area loads tab content; URL updates to `?tab=tasks`
- Lazy loading: each tab's data loads on first switch

**Communication "Resend" click:**
- Trigger: Click resend icon on an email log entry
- Immediate UI: Confirmation popover "Resend this email to [recipients]?" with Confirm/Cancel
- Confirm: `POST /api/v1/communications/:id/resend`
- Success: Toast "Email resent"; new log entry created
- Failure: Error toast

**AI draft "Approve" click:**
- Trigger: Click "Approve" on pending AI draft
- Immediate UI: Button becomes "Sending…"
- API call: `POST /api/v1/communications/:id/approve`
- Success: Draft sent; status updates to "sent"; toast "Email sent"
- Side effects: Communication log entry; notification

**AI draft "Edit & Send" click:**
- Trigger: Click
- Immediate UI: Opens email compose editor with draft pre-filled; AI assumptions bolded; source data shown in side panel with tooltips
- User edits → clicks "Send"
- API call: `POST /api/v1/communications/send` with edited body
- Success: Sent; logged

### 5. Conditional Rendering Logic
- **Role-based visibility:**
  - Client: Overview (limited), Documents (view/upload only), Parties (view only) — no Tasks, no Communications (internal notes hidden), no Edit Transaction
  - Vendor: Documents (own uploads only) — no other tabs
  - FSBO: Overview (simplified), Documents (view/upload/flag), Milestones — no Tasks, no Communications
  - Attorney: All tabs + sign-off actions + legal packet actions; AI items clearly marked
  - Agent/Elf/Team Lead: Full access per their role permissions
  - Admin: Full read access; limited write access
- **State-based:**
  - Closed transactions: all editing disabled; tabs become read-only
  - Paused transactions: editing enabled but task auto-generation paused
  - "Sleeping" tasks only visible in Tasks tab under collapsed section

### 6. Navigation Flows
- **Inbound:** Active Transactions card click, search result, notification link, AI suggestion link
- **Outbound:** Back to Active Transactions (breadcrumb), sidebar links
- **Deep-link:** `?tab=tasks` or `?tab=documents` — sets active tab

### 7–10. Standard patterns
- AI chat panel receives this transaction as context
- Real-time updates for task completion, document uploads, communications by other users
- Edge case: Transaction deleted while viewing → redirect to Active Transactions with toast "Transaction no longer available"

---

# 5. Workflow Section

---

## 5.1 My Task Queue — `/tasks/queue`

**Design reference:** `completed_designs/ve-workflow-my_task_queue.html`

### 1. Page Identity & Access
- **Route:** `/tasks/queue`
- **Page title:** "My Task Queue"
- **Allowed roles:** Agent, Elf, Team Lead, Attorney
- **Redirect rule:** Client/FSBO/Vendor → their portals
- **Auth requirement:** Protected + internal role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/tasks/queue?assignee=me` — tasks assigned to current user, grouped by status/urgency
    - Returns: task list with `{ id, name, transaction_name, transaction_id, client_name, due_date, status, completion_method, assigned_to, ai_reason, ai_confidence }`
  - Optional params: `sort=due_date|urgency|transaction|status`, `filter=overdue|due_today|upcoming|completed`
  - `GET /api/v1/transactions/kpi` — sidebar KPIs
  - `GET /api/v1/ai/briefing`
- **Loading state UI:** Task row skeletons (8–10 rows) grouped under section headers
- **Empty state UI:** "No tasks in your queue" with illustration and "All caught up! Check your dashboard for what's next." message
- **Error state UI:** Error banner with retry

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Sidebar state:** "My Task Queue" nav link active (with badge count for overdue)
- **Topbar state:** AI briefing chip; "+ New Transaction" CTA
- **Page header:** Breadcrumb: Workflow > My Task Queue | "My Task Queue" title + total count pill | "Export" action
- **Tab bar:** All | Overdue (red count) | Due Today (amber count) | Upcoming | Completed
- **Sort control:** Urgency (default) | Due Date | Transaction | Status
- **Primary content area:**
  - Task rows grouped by section:

  **Overdue Section (red header bar):**
  - Each row: checkbox | task name (bold) | transaction name + client (linked) | due date (red, mono) | completion method icon | assigned-to avatar | "..." action menu
  - Section count in header

  **Due Today Section (amber header bar):**
  - Same row pattern; due date in amber

  **Upcoming Section (neutral header):**
  - Same row pattern; due date in default text

  **Completed Section (collapsed by default):**
  - Dimmed rows with strikethrough names; completed_at timestamp

  **Per-row "..." action menu:**
  - Complete Task
  - Edit Task → opens task detail/edit
  - Change Due Date → inline date popover
  - Reassign → dropdown of team members
  - View Transaction → navigate to transaction
  - Skip Task (with confirmation)
  - Delete Task (soft-delete with confirmation)

- **Overlay/modal inventory:**
  - Task edit modal
  - Date change popover
  - Reassign dropdown
  - AI Chat panel

### 4. User Actions & State Transitions

**Task checkbox click (complete):**
- Trigger: Click checkbox
- Immediate UI: Optimistic — checkbox fills, row slides to Completed section with animation
- API call: `PATCH /api/v1/tasks/:id` with `{ status: 'Completed', completed_at: now() }`
- Success: Row confirmed in Completed section; badge counts update; parent transaction may advance
- Failure: Rollback with error toast
- Side effects: Audit log; notifications; dependent tasks may unblock

**Task name click:**
- Trigger: Click task name
- Immediate UI: Navigate to `/tasks/:id` (task detail page)

**Transaction name click:**
- Trigger: Click linked transaction name
- Immediate UI: Navigate to `/transactions/active?highlight=:transactionId`

**"Change Due Date" menu action:**
- Trigger: Select from "..." menu
- Immediate UI: Inline date popover (same as Active Transactions key date edit)
- Save: `PATCH /api/v1/tasks/:id` with `{ due_date: 'new_date' }`
- Side effects: Audit log; may affect dependent task dates

**"Reassign" menu action:**
- Trigger: Select from "..." menu
- Immediate UI: Dropdown of team members (for Team Lead view) or "Cannot reassign" toast for solo agents
- Select member: `PATCH /api/v1/tasks/:id` with `{ assigned_to: 'userId' }`
- Success: Task disappears from "My Queue" (now in other user's queue); toast "Task reassigned to [name]"
- Side effects: Notification to new assignee

**"Skip Task" menu action:**
- Trigger: Select from "..." menu
- Immediate UI: Confirmation popover "Skip this task? It won't count as completed."
- Confirm: `PATCH /api/v1/tasks/:id` with `{ status: 'Skipped' }`
- Success: Task moves to a "Skipped" section (collapsed); toast "Task skipped"
- Side effects: Audit log; does not unblock dependents

### 5. Conditional Rendering Logic
- **Role-based:**
  - Team Lead: toggle "My Tasks" / "Team Tasks" — team view shows all team members' tasks with assignee column
  - Attorney: sees only attorney-related tasks (legal review, packet approval); sign-off tasks have special treatment
  - Agent/Elf: own assigned tasks only
- **State-based:**
  - Overdue section only appears if overdue tasks exist
  - "Vendor cart" view option: group tasks by vendor across transactions (follow up all tasks for one vendor in one email)
- **Responsive:** Task rows become cards on mobile; checkbox stays prominent

### 6. Navigation Flows
- **Inbound:** Sidebar "My Task Queue", notification links, AI suggestion links
- **Outbound:** Task name → `/tasks/:id`; transaction link → `/transactions/active?highlight=:id`
- **Deep-link:** `?filter=overdue`, `?sort=transaction`

### 7. AI Integration Points
- AI briefing counts in topbar
- AI chat panel available (receives task queue context)
- AI confidence shown on AI-recommended tasks
- AI can suggest task prioritization order

### 8–10. Standard patterns
- Real-time: task completions by others update the queue
- Edge case: Large queue (100+ tasks) → paginated with load-more; virtual scrolling

---

## 5.2 Task Detail — `/tasks/:id`

### 1. Page Identity & Access
- **Route:** `/tasks/:id`
- **Page title:** "[Task Name]"
- **Allowed roles:** User assigned to this task, transaction participants, Admin
- **Redirect rule:** No access → 403
- **Auth requirement:** Protected + task access check

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/tasks/:id` — full task data including dependencies, history, AI metadata
  - `GET /api/v1/transactions/:transactionId` — parent transaction summary
- **Loading state UI:** Skeleton
- **Error state UI:** 404 or 403

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Sidebar state:** "My Task Queue" or parent transaction highlighted
- **Page header:**
  - Breadcrumb: Workflow > My Task Queue > [Task Name] (or Deals > [Transaction Name] > Tasks > [Task Name])
  - Task name (editable inline)
  - Status pill (Pending / InProgress / Completed / Blocked / Skipped)
  - Action buttons: Complete Task | Edit | Delete
- **Primary content area:**
  - Task summary card: Description, completion method, due date, assigned to, created date, source (template/AI/manual)
  - If AI-recommended: AI reason card with confidence score, source reference
  - Dependencies section: which tasks this depends on (with status), which tasks depend on this
  - Activity timeline: status changes, edits, comments
  - Parent transaction card: linked transaction with key info
- **Overlay/modal inventory:** Edit Task modal, AI Chat panel

### 4. User Actions
- **"Complete Task" button:** Same as checkbox in queue but from detail view
- **"Edit" button:** Opens edit modal with all task fields
- **Inline name edit:** Click task name → editable text field → blur saves
- **Delete:** Soft-delete with confirmation; task "sleeps"

### 5–10. Standard patterns
- Role-based: read-only for users without edit access
- AI: confidence and reason shown for AI-recommended tasks
- Navigation: breadcrumb back to queue or transaction

---

## 5.3 Closing Calendar — `/closing-calendar`

**Design reference:** `completed_designs/ve-workflow-closing_calendar.html`

### 1. Page Identity & Access
- **Route:** `/closing-calendar`
- **Page title:** "Closing Calendar"
- **Allowed roles:** Agent, Elf, Team Lead, Attorney, Admin
- **Auth requirement:** Protected + internal role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/transactions/calendar?start=:monthStart&end=:monthEnd` — transactions with closing dates in the visible range, including: transaction_id, client_name, address, closing_date, closing_time, status, stage_pill, days_to_close
  - `GET /api/v1/transactions/kpi`
  - `GET /api/v1/ai/briefing`
- **Loading state UI:** Calendar grid skeleton with pulsing day cells
- **Empty state UI:** Calendar renders with no events; sidebar note "No closings scheduled this month"
- **Error state UI:** Error banner with retry

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Sidebar state:** "Closing Calendar" nav link active
- **Topbar state:** Standard
- **Page header:** Breadcrumb: Workflow > Closing Calendar | "Closing Calendar" title | Month/Year selector + navigation arrows (< Month >) | View toggle: Month | Week | List
- **Primary content area:**

  **Month View (default):**
  - Standard calendar grid (7 columns × 5–6 rows)
  - Day cells contain closing event chips: "[Time] Client Name" with status color dot
  - Overdue closings appear in past date cells with red indicator
  - Today's cell highlighted
  - Click on a day → shows expanded day detail (all closings for that day with key info)
  - Click on a closing chip → navigate to `/transactions/:id` or expand inline preview

  **Week View:**
  - 7-column grid with hour slots (business hours)
  - Closing events as blocks showing time, client name, address
  - Time-of-day displayed in mono font; "TBD" shown for unset times

  **List View:**
  - Chronological list of upcoming closings grouped by date
  - Each row: date | time | client name | address | status pill | days to close | agent name (team view)
  - Clickable → navigate to transaction

- **Overlay/modal inventory:**
  - Day detail popover (clicking a day)
  - Quick transaction preview popover (clicking a closing chip)
  - AI Chat panel

### 4. User Actions & State Transitions

**Month navigation (< > arrows):**
- Trigger: Click arrow
- Immediate UI: Calendar slides to new month; new data loads
- API call: `GET /api/v1/transactions/calendar?start=:newMonthStart&end=:newMonthEnd`

**View toggle (Month/Week/List):**
- Trigger: Click toggle
- Immediate UI: Content area switches view; URL updates `?view=week`

**Closing chip click:**
- Trigger: Click on a closing event
- Immediate UI: Shows quick preview popover with: client name, address, closing time, status, key contacts, days to close, "Open Transaction" link
- "Open Transaction" → navigates to `/transactions/:id`

**Day cell click (Month view):**
- Trigger: Click on a day number
- Immediate UI: Expanded panel below the calendar grid showing all closings for that day with full details

### 5. Conditional Rendering Logic
- **Role-based:**
  - Team Lead: shows all team closings with agent name column
  - Attorney: shows only attorney-closing matters
  - Agent/Elf: shows own closings
- **State-based:** Overdue (past) closings show red indicators; today's closings amber; future green
- **Responsive:** Month view → List view forced on mobile (<768px)

### 6. Navigation Flows
- **Inbound:** Sidebar "Closing Calendar", dashboard "Closings This Week" KPI tile click
- **Outbound:** Closing chip → `/transactions/:id`
- **Deep-link:** `?month=2026-04&view=week`

### 7–10. Standard patterns
- AI: briefing chip in topbar; no direct AI actions on calendar
- Real-time: new closings appear when scheduled
- Edge case: Dense days (5+ closings) → chips stack with "+3 more" overflow indicator

---

## 5.4 All Documents — `/documents/all`

**Design reference:** `completed_designs/ve-workflow-all_documents.html`

### 1. Page Identity & Access
- **Route:** `/documents/all`
- **Page title:** "All Documents"
- **Allowed roles:** Agent, Elf, Team Lead, Attorney, Admin
- **Auth requirement:** Protected + internal role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/documents?page=1&limit=30` — all documents across all user's transactions
    - Query params: `search`, `type`, `transaction_id`, `sort=date|name|type|transaction`
  - `GET /api/v1/transactions/kpi`
  - `GET /api/v1/ai/briefing`
- **Loading state UI:** Document row/card skeletons
- **Empty state UI:** "No documents yet" with "Upload your first document" CTA and drag-drop zone
- **Error state UI:** Error banner with retry

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Sidebar state:** "All Documents" nav link active
- **Page header:** Breadcrumb: Workflow > All Documents | "All Documents" title + count pill | "Upload" button | "Export" button
- **Search bar:** Prominent AI-assisted search: "Search by document name, buyer, seller, transaction, or keyword…" with AI search icon
- **Filter bar:** Document type dropdown | Transaction filter | Date range | Status (all/pending/processed/signed)
- **Primary content area:**
  - Data table with columns: Document Name | Type | Transaction | Uploaded By | Date | Version | Status | Signature Status | Actions
  - Each row: clickable name (opens preview/download) | type badge | transaction name (linked) | uploader name | upload date (mono) | version number | status pill | signature badge | action icons (download, email, e-sign, rename, delete)
  - Sort by clicking column headers
  - Pagination at bottom (30 per page)

- **Overlay/modal inventory:**
  - Document preview modal (PDF/image viewer)
  - Document email modal (select recipients, subject, body)
  - Send for E-Signature modal
  - Version History side panel
  - Upload modal with AI classification
  - AI Chat panel

### 4. User Actions & State Transitions

**AI search input:**
- Trigger: Type in search field (debounced 300ms)
- Immediate UI: Results filter in real-time; AI may show contextual suggestion: "Did you mean the inspection report for the Smith transaction?"
- API call: `GET /api/v1/documents?search=:query` — AI-powered search across document content, names, metadata, and related transaction data
- Success: Filtered results with search term highlighted
- No results: "No documents match your search" with suggestions

**Document name click:**
- Trigger: Click
- Immediate UI: Opens document preview modal (PDF viewer for PDFs, image viewer for images, download prompt for other types)

**Transaction link click:**
- Trigger: Click transaction name in a row
- Immediate UI: Navigate to `/transactions/:id?tab=documents`

**Upload button click:**
- Trigger: Click "Upload" button or drag-drop anywhere on page
- Immediate UI: Opens upload modal or triggers global drag-drop intake
- AI identifies document type, suggests name, asks which transaction it belongs to
- See Cross-Cutting Workflow D for full document lifecycle

**"Email" action click:**
- Trigger: Click email icon on a document row
- Immediate UI: Opens email compose modal with document pre-attached
- Fields: To (suggest transaction participants), CC, Subject (auto-filled), Body (template)
- Send: `POST /api/v1/communications/send` with attachment
- Success: Toast "Email sent"; communication log entry
- Side effects: Audit log

**"E-Sign" action click:**
- Trigger: Click
- Immediate UI: Opens e-signature modal: select recipients, signing order
- If no e-sign provider connected → toast "Connect an e-signature provider in your profile settings" with link to `/profile`
- Send: `POST /api/v1/documents/:id/esign` with recipients
- Success: Toast "Sent for signature"; document status → "Sent for Signature"
- Side effects: Tracking initiated; audit log

**"Delete" action click:**
- Trigger: Click (for Agent/Team Lead/Admin only)
- Immediate UI: Confirmation dialog "This document will be archived. Are you sure?"
- Confirm: `DELETE /api/v1/documents/:id` (soft delete)
- Success: Row removes from list (or shows "Archived" badge); toast "Document archived"
- Side effects: Audit log with before/after

**"Version History" action click:**
- Trigger: Click version number or dedicated icon
- Immediate UI: Side panel with version list (newest first): version number, date, uploaded by, change description. Each version downloadable.

### 5. Conditional Rendering Logic
- **Role-based:**
  - Agent/Team Lead/Admin: full actions (upload, email, e-sign, delete)
  - Elf: upload, email, e-sign, no delete
  - Attorney: upload (legal packets), email, view — delete only own uploads
  - Vendor/Client/FSBO: do NOT see this page (redirected)
- **State-based:**
  - Signed documents show green "Signed" badge
  - Pending signature shows amber "Awaiting Signature" badge
  - Legacy/outdated documents show gray "Legacy" badge
- **Responsive:** Table → card list on mobile; search stays prominent

### 6–10. Standard patterns
- AI search provides intelligent cross-transaction document finding
- Real-time: new uploads appear; signature status updates
- Edge case: Large document libraries (1000+) → server-side pagination required; AI search essential for findability

---

# 6. Intelligence Section

---

## 6.1 AI Suggestions — `/ai-suggestions`

**Design reference:** `completed_designs/ve-intelligence-ai_suggestions.html`

### 1. Page Identity & Access
- **Route:** `/ai-suggestions`
- **Page title:** "AI Suggestions"
- **Allowed roles:** Agent, Elf, Team Lead, Attorney
- **Auth requirement:** Protected + internal role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/ai/suggestions?page=1&limit=20` — pending AI suggestions:
    - Each suggestion: `{ id, type, title, description, transaction_name, transaction_id, confidence, source, reason, suggested_action, created_at }`
    - Types: task_add, task_remove, deadline_adjust, email_draft, document_request, risk_alert
  - `GET /api/v1/ai/suggestions/stats` — summary: pending count, accepted this week, rejected this week, confidence distribution
- **Loading state UI:** Suggestion card skeletons
- **Empty state UI:** "No pending AI suggestions" with checkmark illustration and "AI is monitoring your transactions. New suggestions will appear here."
- **Error state UI:** Error banner with retry

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Sidebar state:** "AI Suggestions" nav link active (with badge count)
- **Page header:** Breadcrumb: Intelligence > AI Suggestions | "AI Suggestions" title + pending count pill
- **Filter bar:** Type filter (All | Tasks | Deadlines | Emails | Documents | Risks) | Confidence slider (show only above X%) | Transaction filter
- **Primary content area:**
  - Suggestion cards stacked vertically:

  **Each suggestion card:**
  - Left: Type icon (color-coded) + confidence ring (percentage)
  - Center:
    - Title: e.g., "Add task: Order Home Warranty" or "Deadline risk: Inspection response overdue"
    - Description: 2–3 line explanation
    - Source: "Based on: [document name / pattern / prior behavior]"
    - Transaction link: "[Client Name] — [Address]"
  - Right: Action buttons:
    - **Accept** (green) — applies the suggestion
    - **Edit & Accept** — opens edit modal with suggestion pre-filled for modification
    - **Dismiss** (gray) — rejects the suggestion with optional reason
  - For task suggestions: "Apply to this transaction" | "Apply to all future transactions" radio options
  - For email drafts: "Preview draft" link opens side-by-side review

- **Overlay/modal inventory:**
  - Edit Suggestion modal (modify details before accepting)
  - Email draft preview (side-by-side view)
  - AI Chat panel

### 4. User Actions & State Transitions

**"Accept" button click:**
- Trigger: Click
- Immediate UI: Card slides out with success animation; count decrements
- API call: `POST /api/v1/ai/suggestions/:id/accept` with `{ scope: 'transaction' | 'all_future' }`
- Success: Suggestion applied (task added, date adjusted, email sent, etc.); toast "Suggestion applied"
- Failure: Error toast; card returns
- Side effects: Audit log; if `scope=all_future` → team lead must approve for team-wide changes (redirects to approval queue)

**"Dismiss" button click:**
- Trigger: Click
- Immediate UI: Card dims; "Why?" optional text input appears
- API call: `POST /api/v1/ai/suggestions/:id/dismiss` with `{ reason: 'optional text' }`
- Success: Card removes; toast "Suggestion dismissed"
- Side effects: AI learning system records rejection reason for future improvement

**"Edit & Accept" click:**
- Trigger: Click
- Immediate UI: Opens edit modal with suggestion details pre-filled (e.g., task name, due date, description)
- User modifies → clicks "Apply"
- API call: `POST /api/v1/ai/suggestions/:id/accept` with modified payload
- Success: Applied with modifications; toast

**Confidence slider change:**
- Trigger: Drag slider
- Immediate UI: Cards filter to show only suggestions at or above the threshold
- Client-side filter (no API call)

### 5. Conditional Rendering Logic
- **Role-based:**
  - Agent: sees suggestions for own transactions; "Apply to all future" requires confirmation
  - Team Lead: sees team-wide suggestions; "Apply to all future" affects team templates (preview of affected transactions shown before confirmation)
  - Attorney: sees legal-relevant suggestions only; AI guardrails enforced (no legal judgment suggestions)
  - Elf: sees suggestions for assigned transactions
- **State-based:**
  - High-confidence suggestions (≥90%) shown with green border
  - Low-confidence suggestions (<75%) shown with amber "Needs review" badge
  - Risk alerts shown with red indicator regardless of confidence

### 6–10. Standard patterns
- AI chat panel available for asking about suggestions
- Real-time: new suggestions appear as AI processes transactions
- Edge case: Bulk actions — "Accept all above 90% confidence" button for efficiency (with preview)

---

## 6.2 Analytics — `/analytics`

**Design reference:** `completed_designs/ve-intelligence-analytics.html`

### 1. Page Identity & Access
- **Route:** `/analytics`
- **Page title:** "Analytics"
- **Allowed roles:** Agent, Elf, Team Lead, Admin
- **Auth requirement:** Protected + internal role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/analytics/dashboard` — aggregated analytics:
    - Closings by month (bar chart data)
    - Revenue/GCI trend (line chart)
    - Task completion rates (pie chart)
    - Average days to close (trend line)
    - Transaction type distribution
    - AI suggestion acceptance rate
    - Top reasons for deal drift
  - Optional params: `period=month|quarter|year`, `agent_id` (for team view)
- **Loading state UI:** Chart placeholder skeletons with pulsing gray rectangles
- **Empty state UI:** Charts render with zero data and "Complete your first transaction to see analytics" message
- **Error state UI:** Error banner with retry

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Sidebar state:** "Analytics" nav link active
- **Page header:** Breadcrumb: Intelligence > Analytics | "Analytics" title | Period selector (This Month | This Quarter | This Year | Custom Range) | Export button
- **Primary content area:**
  - KPI summary row: Total Closings (period) | Total Volume | Avg Days to Close | Task Completion Rate | AI Acceptance Rate
  - Chart grid (2×3 or 3×2):
    1. Closings by Month (bar chart)
    2. Revenue/GCI Trend (line chart)
    3. Transaction Type Distribution (donut chart)
    4. Task Completion Rate Over Time (line chart)
    5. AI Suggestion Effectiveness (accepted/rejected/modified bar chart)
    6. Deal Drift Reasons (horizontal bar chart)
  - Data table below charts: transaction-level detail supporting the above charts, sortable/filterable

### 4. User Actions
- **Period selector change:** Reloads all charts/data for selected period
- **Chart click (drill-down):** Clicking a bar/segment filters the data table below to show relevant transactions
- **Export:** Downloads analytics report as CSV or PDF

### 5. Conditional Rendering Logic
- **Role-based:**
  - Team Lead: "Agent" filter dropdown to view per-agent analytics; team aggregate default
  - Admin: tenant-wide analytics; role-based breakdown chart added
- **Responsive:** Charts stack vertically on mobile; responsive chart library (recharts)

### 6–10. Standard patterns
- No direct AI actions; AI acceptance rate chart is informational
- Data refreshes on period change; no real-time updates needed (analytics are computed)

---

## 6.3 Settings — `/settings`

> **⚠ Superseded (May 2026 redesign — see `ACCOUNT_MODAL_REDESIGN_PLAN.md`).** Settings is no longer a single page. Personal preferences (Profile/identity, Notifications, My Closing Checklist Templates, My Tagged Notes, My Preferred Vendors, My Internal Resources, Help & tour) now live in the shared **Account modal** opened from the avatar menu / footer gear. Tenant/workspace configuration (Company, Branding, AI configuration, Email integrations, E-signature, Danger Zone) lives on the new **Organization page** at `/organization`. The **Task Templates** stub was deleted (its sole home is `/admin/task-templates`). `/settings`, `/client/settings`, `/fsbo/settings` (+ `?section=`) are kept as routes that open the Account modal. The section descriptions below remain accurate per-section, but their *location* has moved.

### 1. Page Identity & Access
- **Route:** `/settings`
- **Page title:** "Settings"
- **Allowed roles:** Any authenticated user. The route is registered without `ProtectedRoute` (unlike `/team` and `/admin/*`), so TC/Elf, Team Lead, and Admin all see the same page with the same controls.
- **Redirect rule:** None role-specific — the page renders identically for every role.
- **Auth requirement:** Protected (auth required, no role gating).

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/users/me` — current user (for hero greeting / ownership scoping).
  - `GET /api/v1/integrations` — provider connection status (Gmail, Outlook, DocuSign). Powers Snapshot Inbox/E-Sign tile counts and provider rows. Re-fetched on every Refresh click.
- **Loading state UI:** Inline skeleton on the Email Integrations and E-Signature cards while integrations load. Hero and other sections render statically.
- **Empty state UI:** N/A — Settings page always has its hero and seven sections.
- **Error state UI:** Red banner above the Email Integrations rows when the integrations API errors; per-action red toasts for connect / disconnect failures.

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell.
- **Sidebar state:** No nav link is active (Settings is reached from the user-avatar menu in the topbar or the user profile card in the sidebar footer).
- **Page header:**
  - Hero panel — orange-gradient top stripe, serif "Settings" title, brief subhead.
  - **Snapshot tiles** — four clickable tiles below the title: **Inbox** (`connected/total` count from integrations), **E-Sign** (DocuSign connection state), **Credits** (hardcoded `250 of 1,000` — placeholder), **Templates** (hardcoded `5` — placeholder). Each tile scroll-jumps to its matching section header below.
- **Sticky left-rail nav (`Sections`):** appears on screens ≥ 1024 px. IntersectionObserver-driven scroll-spy highlights the active section in orange. Click any item to scroll-jump.
- **Primary content area — single scrolling document with seven sections (display order):**

  1. **Company.** Three text fields with hardcoded defaults (Company Name "Velvet Elves Realty", Contact Email, Phone) + **Save changes** button. *Visual-only — no onClick, no persistence.*

  2. **Email Integrations** *(Milestone 4.1).* Section header has a **Refresh** button (spinner during fetch). Provider rows for **Gmail** and **Outlook** (iCloud row hidden behind `SHOW_ICLOUD = false`). Each row shows brand glyph, provider name, connected email or help text, "Connected" green pill + connection date if active, and a **Connect** (orange) or **Disconnect** (outline) button. Errors render as a red banner above the rows. *Fully wired — see §4 actions below.*

  3. **E-Signature.** Single DocuSign tile with logo, account email, connection date, and **Connect** / **Disconnect** button. Connect launches the 3-step wizard modal (Intro → Authorize popup → Done); see §27.14 in the testing doc / `ConnectEsignWizardModal` for full flow. Disconnect uses a native `confirm()` dialog. *Fully wired.*

  4. **Branding.** Logo upload tile (dashed placeholder + Upload logo button), Primary Color field (default `#E26812`) with swatch preview, Display Name field (default "Velvet Elves AI"), **Save branding** button. *Visual-only — no fields persist.*

  5. **AI Configuration.** Hero strip "AI Credits — 250 of 1,000 remaining" with 25% progress bar and **Upgrade plan** button. Three toggle rows: Auto-parse uploaded documents (on), Task recommendations (on), Smart email drafts (off). *Visual-only — toggles flip locally but do not persist; credit numbers are hardcoded.*

  6. **Task Templates.** Card header has an **Import** button. Hardcoded list of 5 templates: Buyer Standard (12), Seller Standard (14), Dual Agency (18), Lease (8), Commercial (22), each with an **Edit** button. *Visual-only — neither Edit nor Import is wired. Real template management lives at `/admin/task-templates` (§10.3).*

  7. **Help & Tour.** "Replay the guided walkthrough" hero card with **Start tour** button. *Fully wired — clears the user's tour-completed flag and immediately restarts the role-aware product tour (see §14.10).*

- **Overlay/modal inventory:**
  - `ConnectEsignWizardModal` — opens from the E-Signature **Connect** button.
  - Native browser `confirm()` — used by Email Integrations and E-Signature **Disconnect** to prevent accidental disconnects.

### 4. User Actions & State Transitions

**Snapshot tile click (Inbox / E-Sign / Credits / Templates):**
- Trigger: Click.
- Immediate UI: Smooth scroll-jump to the matching section header below.
- API call: None.

**Section-rail click (sticky left-rail nav):**
- Trigger: Click an item.
- Immediate UI: Scroll-jump; the IntersectionObserver picks up the new active section once it crosses the threshold.
- API call: None.

**Email Integrations — Refresh button:**
- Trigger: Click.
- Immediate UI: Spinner on the button; integrations list re-fetches.
- API call: `GET /api/v1/integrations`.
- Success: Provider rows re-render with fresh state.
- Failure: Red banner above the rows with the error message.

**Email Integrations — Connect (Gmail / Outlook):**
- Trigger: Click an unconnected provider's Connect button.
- Immediate UI: OAuth popup opens.
- API call: Provider OAuth round-trip via `useEmailProviderOAuth`; on success the integrations list is invalidated and re-fetched.
- Success: Row flips to "Connected" green pill + connection date. Toast `"{Provider} connected!"`.
- Failure / cancel: Destructive toast; row stays unconnected.

**Email Integrations — Disconnect:**
- Trigger: Click Disconnect.
- Immediate UI: Native browser `confirm()` dialog: "Disconnecting … will stop syncing inbound mail and AI email automation will not be able to send …".
- API call: `DELETE /api/v1/integrations/:id` (only after confirm).
- Success: Row reverts to unconnected; success toast.
- Failure: Red banner above the rows.

**E-Signature — Connect:**
- Trigger: Click Connect.
- Immediate UI: `ConnectEsignWizardModal` opens (Intro → Authorize popup → Done).
- API calls: DocuSign OAuth via `useDocuSignOAuth`; integrations refetch on success.
- Success: Wizard advances to Done step; close handler flips the tile to Connected + green pill.
- Failure: Wizard surfaces inline error and Retry button.

**E-Signature — Disconnect:**
- Trigger: Click Disconnect.
- Immediate UI: Native `confirm()` dialog warning that future Send for Signature attempts will fail.
- API call: `DELETE /api/v1/integrations/:docusignId`.
- Success: Tile reverts; toast confirms.

**Help & Tour — Start tour button:**
- Trigger: Click.
- Immediate UI: Tour-completion key for this user is cleared (`localStorage.velvet_elves_tour_completed:{userId}`); `TourProvider.start()` is invoked.
- Side effect: Role-aware product tour fires immediately on top of the Settings page.

**Visual-only controls (Company / Branding / AI Configuration / Task Templates):**
- Click any Save / Upload / Edit / Import button → no-op (no onClick wiring). Toggles flip local state but do NOT call any API; refresh resets them.

### 5. Conditional Rendering Logic
- **Role-based visibility:** None today. *Planned:* gate Branding, Task Templates, and AI Configuration to Admin / Team Lead.
- **State-based visibility:**
  - Provider rows: "Connected" pill, account email, and Disconnect button only render once an integration is linked. Unconnected rows show help text + Connect button.
  - iCloud row: hidden behind `SHOW_ICLOUD = false` flag.
  - Snapshot Inbox tile shows live `connected/total` from `/api/v1/integrations`; E-Sign tile flips green when DocuSign is connected; Credits + Templates tiles are hardcoded.
- **Feature flags:** `SHOW_ICLOUD` (off). No other tenant flags surfaced on this page.
- **Responsive behavior:** Sticky left-rail nav hidden below 1024 px; Snapshot tiles wrap to 2x2 on narrow screens. Card body content stacks vertically.

### 6. Navigation Flows
- **Inbound routes:** Topbar avatar menu → Settings; sidebar profile card → Settings; "Connect Gmail / DocuSign" prompts elsewhere (e.g. AI Email Review error toast: "No active gmail integration") deep-link here.
- **Outbound routes:**
  - `/admin/task-templates` — *planned* link from the Task Templates section once that placeholder is replaced.
  - DocuSign OAuth popup → returns to `/settings` (modal closes on success).
- **Deep-link support:** Hash fragments (`/settings#email-integrations`, `/settings#help-tour`) supported via section IDs; query-string deep-links not yet implemented.
- **Back navigation:** Browser back from Settings returns to the previous page.

### 7. AI Integration Points
- **AI data on page:** AI Configuration card displays AI Credits remaining (hardcoded today; backend hook planned).
- **AI actions available:** None directly. The "Smart email drafts" toggle is a UI placeholder for the planned auto-send threshold setting.
- **AI confidence display:** None.
- **AI guardrails:** Not surfaced in UI. Backend `tenants.settings_json.ai_email` (tone, disclaimer, escalation hours, auto-send threshold) is admin-API only — no Settings UI exists for these yet.
- **AI chat panel:** Available via the topbar Ask AI button while on this page.

### 8. Real-Time & Notification Behavior
- **Live updates:** Integrations list re-fetches on Refresh click and after any Connect/Disconnect action. No background polling.
- **Notification triggers:** None.
- **Toast/alert patterns:** Success/failure toasts for connect, disconnect, and refresh. Red banner for integrations API errors.

### 9. Cross-Page Relationships
- **Shared state:** Provider connection status here drives the green "Connected" badges in the Onboarding wizard's Email step and the AI Email Review queue's send affordances. Disconnecting Gmail here will cause AI Email Review's Approve & Send to fail with "No active gmail integration".
- **Dashboard deep-linking:** None.
- **Data dependencies:** Email integrations are a precondition for AI Email Review (§6.4) and Email Document modal (§5.4 / 27.9). DocuSign integration is a precondition for Send for Signature (§5.4 / 27.8 / 27.14).

### 10. Edge Cases & Special Behaviors
- **Visual-only sections persist on refresh:** Company / Branding / AI Configuration / Task Templates fields all reset to their hardcoded defaults on refresh — flag clearly to clients to avoid expectations of persistence.
- **Popup-blocked OAuth:** Gmail / Outlook / DocuSign OAuth popups can be blocked by Safari and Brave. *Planned:* fallback redirect-based OAuth.
- **Stale integration list:** If a popup completes successfully but the post-OAuth re-fetch fails (network blip), the row may stay "Unconnected" until the user clicks Refresh.
- **Concurrent disconnects:** No optimistic UI; the row stays in its current state until the API confirms the disconnect.
- **Tour replay during a tour:** Clicking Start tour while a tour is already running re-starts from step 1.

---

## 6.4 AI Email Review — `/ai-emails`

> **As-built (May 2026):** Milestone 4.2 surface. Powered by Email Integrations configured in §6.3 (Milestone 4.1). The page replaces the older inline AI Email drawer concept and is now the canonical review queue for AI-prepared replies.

### 1. Page Identity & Access
- **Route:** `/ai-emails` (canonical). `/ai-emails/:logId` is registered for deep-links but the param is NOT yet read by the page (planned).
- **Page title:** "AI Email Review"
- **Allowed roles:** Any authenticated user can navigate to the URL. The list is server-scoped to drafts the caller's tenant + role can act on (Agent / TC / TeamLead / Admin who owns the file). FSBO and Attorney roles do not see the sidebar entry.
- **Redirect rule:** None client-side.
- **Auth requirement:** Protected.

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** At least one connected email provider in Settings → Email Integrations is required for Approve & Send / Edit & Send to succeed end-to-end. With no provider, drafts still appear but actions surface "No active gmail integration" toast.
- **API endpoints on mount:**
  - `GET /api/v1/ai-emails/drafts` — list all drafts for the caller's tenant + role scope. Polled every 60 seconds (`refetchInterval: 60_000`, `staleTime: 30_000`).
  - `GET /api/v1/ai-emails/drafts/:id/inbound` — lazy-loaded when a draft is selected; populates the Original Inbound card.
- **Loading state UI:** Four pulsing grey skeleton rows in the list pane. Lazy skeleton in the Original Inbound card.
- **Empty state UI:**
  - All drafts empty → right pane: Mail icon + "Inbox is clear — When the AI prepares a reply that needs your sign-off, it will land here for review before sending."
  - Filter slice empty (drafts exist, current tab is empty) → right pane: "Nothing in this view — Try a different filter, or wait for the next AI-prepared reply to land here."
- **Error state UI:** Centered "Couldn't load drafts." card with a "Try again" link.

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell.
- **Sidebar state:** Sidebar → Intelligence → "AI Email Review" highlighted. Entry only renders for Agent / TC / Team Lead / Admin.
- **Page header:**
  - Breadcrumb: `Intelligence > AI Email Review`.
  - Title `AI Email Review` + orange count pill (`{N} drafts` / `1 draft`).
  - Right cluster (md+ only): muted `Updated {Xm} ago` timestamp + **Refresh** button (spinner during fetch).
- **Filter tabs (under header):** five tabs with numeric count badges:
  1. **All** — every draft.
  2. **Needs Review** (red badge when count > 0) — `ai_kind === "uncertain"` OR has flagged assumptions.
  3. **Ready to Send** — confidence ≥ 80%, kind ≠ "uncertain", no flagged assumptions.
  4. **Low Confidence** — confidence < 50%.
  5. **Escalated** (red badge when count > 0) — past the escalation deadline.
- **Two-pane layout (≥ 1024 px):**
  - **List pane (left, ~320 px):** vertical list of draft rows divided by hairlines. No search / sort / bulk-action UI. Tabs are the only filter.
  - **Detail pane (right, fluid):** hero header + body grid (left) + right rail (right, 340 px) holding AI Verified From + Original Inbound cards. On mobile, the panes stack with the list above the detail.
- **Per-row anatomy (list pane):**
  - Left edge: orange bar when active; light-grey hover.
  - Status dot: green (high), amber (medium), red (low / escalated), grey (unknown).
  - Subject (bolder when selected, falls back to "(no subject)").
  - Recipient email(s) — monospaced, truncated.
  - Pill row: Kind label (color-coded), Confidence percent, Escalated red pill if applicable.
  - Right side: relative timestamp + chevron on hover/active.
- **Detail pane — hero header:** AI Draft sparkles badge + Kind pill + Confidence meter (label + tiny progress bar + percent) + Escalated pill if applicable. Subject in serif. To/Cc lines (Cc rendered only when present; the file owner agent is auto-CC'd by default).
- **Detail pane — body grid (left):** AI-drafted reply rendered as plain text. Hedged phrases wrapped in amber `<mark>` tags. If flagged assumptions exist, an amber-bordered "Flagged assumptions" panel lists each one explicitly below the body.
- **Detail pane — right rail:**
  - **AI Verified From** card — orange-eyebrowed; lists every `key: value` the AI cited (address, closing_date, status, document names, etc.). Empty case → orange dashed warning: "No source data was cited for this draft. Treat the body as a generic response and verify each fact manually."
  - **Original Inbound** card — sender, timestamp, subject, body of the inbound that triggered the draft. Lazy-loaded with skeleton; failure case → "Couldn't load the original inbound message."
- **Action footer (detail pane, bottom):**
  - **View mode:** Approve & Send (orange primary), Edit (ghost), Regenerate (ghost), Discard (ghost, red).
  - **Edit mode:** Subject + Body editable (live char counter). Send Edit (orange primary), Cancel (ghost).
- **Overlay/modal inventory:** AlertDialog for Discard confirmation: "Discard this AI draft? The draft will be removed from your review queue. The original inbound message stays in your communication log."

### 4. User Actions & State Transitions

**Refresh button:**
- Trigger: Click.
- Immediate UI: Button spinner; list re-fetches.
- API call: `GET /api/v1/ai-emails/drafts`.

**Filter tab click:**
- Trigger: Click any of the 5 tabs.
- Immediate UI: List narrows; selection persists if the selected draft is still in the new slice; otherwise the first row of the new slice is auto-selected.

**Row click (list pane):**
- Trigger: Click a row.
- Immediate UI: Row gains orange left edge; detail pane loads. `GET /api/v1/ai-emails/drafts/:id/inbound` fires lazily for the Original Inbound card.

**Approve & Send (view mode):**
- Trigger: Click.
- Immediate UI: Button spinner.
- API call: `POST /api/v1/ai-emails/drafts/:id/approve`.
- Success: Toast "Sent — AI reply approved and delivered."; list invalidated immediately so the row disappears.
- Failure: Red toast with the API error verbatim (e.g. "Send failed — No active gmail integration."). Detail pane stays in view mode.

**Edit (view mode):**
- Trigger: Click.
- Immediate UI: Body card flips to editable mode; Subject and Body inputs render with live char counter.

**Send Edit (edit mode):**
- Trigger: Click.
- Immediate UI: Button spinner.
- API call: `POST /api/v1/ai-emails/drafts/:id/edit-and-send` with edited subject/body.
- Success: Toast "Sent — Edited reply delivered."; list invalidated; detail pane returns to empty state. Server clears flagged assumptions for this draft.
- Failure: Red toast; detail pane stays in edit mode with the user's draft intact.

**Cancel (edit mode):**
- Trigger: Click.
- Immediate UI: Reverts to view mode; local edits discarded.

**Regenerate (view mode):**
- Trigger: Click.
- Immediate UI: Spinner on the icon while running.
- API call: `POST /api/v1/ai-emails/drafts/:id/regenerate` — the AI re-drafts from the original inbound.
- Success: Toast "Regenerated — A fresh draft is ready for review."; the same row is replaced in the list with the new draft. Detail pane refreshes.
- Failure: Red toast with API error.

**Discard (view mode):**
- Trigger: Click.
- Immediate UI: AlertDialog opens.
- Cancel: dialog closes, no API call.
- Confirm: `POST /api/v1/ai-emails/drafts/:id/discard`. Success → row disappears, toast confirms. The inbound communication log is preserved server-side.

### 5. Conditional Rendering Logic
- **Role-based visibility:** Sidebar entry only for Agent / TC / Team Lead / Admin. Server enforces who can act on which drafts; UI does not pre-disable buttons by role (unauthorized clicks return error toasts).
- **State-based visibility:**
  - Escalated pill renders only when `escalation_due_at` has passed.
  - Flagged assumptions panel renders only when at least one assumption exists.
  - Cc line renders only when CC recipients exist.
  - Action footer hides Approve / Regenerate / Discard while in edit mode (replaced with Send Edit / Cancel).
- **Feature flags:** None on this page today. Tenant `settings_json.ai_email.auto_send_threshold` is consumed server-side; not surfaced in UI.
- **Responsive behavior:** Below 1024 px the list and detail panes stack; above 1024 px they sit side-by-side with the list at ~320 px.

### 6. Navigation Flows
- **Inbound routes:** Sidebar → Intelligence → AI Email Review. Topbar bell → "N AI drafts awaiting review" callout. Notifications page row click.
- **Outbound routes:** None directly (no per-draft "Open transaction" link yet — *planned*).
- **Deep-link support:** `/ai-emails/:logId` route is registered but the param is NOT wired to auto-select the draft. *Planned* hand-off: notifications open the exact draft.
- **Back navigation:** Standard browser back; selection state is not preserved in URL.

### 7. AI Integration Points
- **AI data on page:** Every draft is the AI's output. Confidence percent, kind taxonomy (Factual question / Document request / Vendor reply / Uncertain — review carefully / Other), flagged assumptions, and AI Verified From source list are all surfaced.
- **AI actions available:** Approve & Send, Edit & Send (clears flags), Regenerate (re-drafts), Discard.
- **AI confidence display:** Status dot (list pane) + Confidence meter (detail header). Five-tab taxonomy partitions the queue by confidence + flag state.
- **AI guardrails:**
  - "AI Verified From" rail surfaces every fact the AI cited so the reviewer can verify before sending.
  - Empty AI Verified From triggers an explicit warning card.
  - Flagged assumptions are highlighted inline AND listed explicitly in a side panel.
  - Drafts past `escalation_due_at` are visually flagged on both panes.
- **AI chat panel:** Available via topbar Ask AI; not directly integrated with the draft pane.

### 8. Real-Time & Notification Behavior
- **Live updates:** 60-second polling on the drafts list (no websocket). After every Approve / Edit & Send / Regenerate / Discard, the list is invalidated immediately so the acted-on draft disappears without waiting for the next poll. Bell badge polls on the same 60 s cadence.
- **Notification triggers:** New drafts arriving fire the "N AI drafts awaiting review" badge in the topbar bell.
- **Toast/alert patterns:** Per-action success ("Sent — …") and failure ("Send failed — {api error}") toasts. AlertDialog for Discard confirmation.

### 9. Cross-Page Relationships
- **Shared state:** Email integrations from §6.3 are the precondition for sending. DocuSign integration is unrelated to this page.
- **Audit trail:** Every Approve / Edit & Send / Regenerate / Discard / Escalate writes to `audit_logs` server-side. The user-visible signals are the toast and the row disappearing from the queue.
- **CC behavior:** The owner agent is always CC'd on outbound sends so they keep a copy in their Sent folder. Visible in the To/Cc header before sending.

### 10. Edge Cases & Special Behaviors
- **No connected email provider:** Drafts still appear, but Approve & Send / Edit & Send fail with "No active gmail integration". *Planned:* surface a banner at the top of the page when no provider is connected, with a "Connect inbox" deep-link.
- **Draft acted on by another reviewer mid-poll:** The 60-second poll invalidates the local cache; the row disappears on the next refetch.
- **Selected draft removed by another action:** First row of the current slice is auto-selected so the right pane is never stranded.
- **Edit & Send clears flagged assumptions:** Server clears them because the human just rewrote the content. Regenerate keeps flagged assumptions because the AI is generating a new draft.
- **Escalated drafts:** Past `escalation_due_at` they bump the Escalated tab counter (red badge) and gain a red pill in both panes. They do not auto-send — the reviewer still has to act on them.
- **Long bodies:** Body card scrolls inside its grid cell; right rail and footer remain fixed.
- **Original Inbound load failure:** Card renders an error string but does not block the rest of the page.

---

# 7. Attorney Workspace

---

## 7.1 Attorney Queue — `/attorney/queue`

### 1. Page Identity & Access
- **Route:** `/attorney/queue`
- **Page title:** "Attorney Matter Queue"
- **Allowed roles:** Attorney
- **Redirect rule:** Non-attorney → `/dashboard`
- **Auth requirement:** Protected + Attorney role

### 2–3. Entry & Layout
- This route overlaps heavily with the Attorney Dashboard (§3.4). For MVP, `/attorney/queue` redirects to `/dashboard/attorney` which contains the full matter queue with filter tabs.
- If implemented as a separate page in future: same data, layout, and actions as the Attorney Dashboard matter cards, but without the hero card and production metrics — focused purely on the queue.

### 4–10. See Attorney Dashboard (§3.4) for all action, rendering, navigation, and AI specifications.

---

## 7.2 Attorney Releases — `/attorney/releases`

### 1. Page Identity & Access
- **Route:** `/attorney/releases`
- **Page title:** "Release Queue"
- **Allowed roles:** Attorney
- **Auth requirement:** Protected + Attorney role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/attorney/releases` — transactions/matters where all sign-offs are complete and packets are ready for release
  - Each entry: matter name, client, closing date, packet contents, sign-off status, release readiness
- **Loading state UI:** Release card skeletons
- **Empty state UI:** "No packets ready for release" with guidance text

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Page header:** "Release Queue" title + count pill
- **Primary content area:**
  - Release-ready matter cards:
    - Matter name, status ("Ready to Release" green pill)
    - Packet contents list (documents included)
    - All sign-off checkboxes shown as completed (green checks)
    - "Release Packet" primary action button
    - "Hold" secondary button (moves back to review queue)
    - Release conditions summary (state rules, recording timing, disbursement check)

### 4. User Actions

**"Release Packet" click:**
- Trigger: Click
- Immediate UI: Confirmation modal with: recipient list, document list, release conditions, recording timeline, disbursement timing check
- Confirm: `POST /api/v1/attorney/release-packet`
- Success: Toast "Packet released"; matter moves to completed; notifications sent
- Side effects: Communication log; audit log; notifications to all parties

**"Hold" click:**
- Trigger: Click
- Immediate UI: Reason input popover → submit
- API call: `PATCH /api/v1/attorney/matters/:id` with `{ status: 'needs_review', hold_reason: 'text' }`
- Success: Matter returns to review queue; toast "Matter held for review"

### 5. Conditional Rendering Logic
- AI guardrails: "Release Packet" is ALWAYS human-initiated. No AI auto-release. The confirmation modal explicitly states "This is a legal release requiring your authorization."

### 6–10. Standard patterns
- Navigation: Inbound from attorney dashboard "Open release queue" CTA; outbound to completed matters
- No AI actions on release (human-owned)

---

## 7.3 State Rules — `/attorney/state-rules`

### 1. Page Identity & Access
- **Route:** `/attorney/state-rules`
- **Page title:** "State Rules Reference"
- **Allowed roles:** Attorney, Admin
- **Auth requirement:** Protected + Attorney or Admin role

### 2–3. Entry & Layout
- Reference page displaying state-specific closing rules
- **API endpoints:** `GET /api/v1/attorney/state-rules?state=:state`
- **Content:** Organized by state with sections for: Closing mode (attorney vs. title/escrow), Recording timelines, Disbursement timing, Same-day release checks, Required attorney involvement, Local forms/compliance
- **Read-only reference** — Admin can edit rules via `/admin/tenant` settings

### 4–10. Primarily informational; click state to view its rules; search across rules. Linkable from attorney dashboard state rules modal.

---

## 7.4 Recording Calendar — `/attorney/recording-calendar`

### 1. Page Identity & Access
- **Route:** `/attorney/recording-calendar`
- **Page title:** "Recording Calendar"
- **Allowed roles:** Attorney
- **Auth requirement:** Protected + Attorney role

### 2–3. Entry & Layout
- Similar to Closing Calendar but focused on recording dates (when deeds/documents are recorded with the county)
- **API endpoints:** `GET /api/v1/attorney/recording-calendar?start=:start&end=:end`
- Calendar view showing recording dates, disbursement dates, and associated matter deadlines
- Same Month/Week/List views as Closing Calendar

### 4–10. Same interaction patterns as Closing Calendar (§5.3) with attorney-specific context

---

# 8. FSBO Customer Workspace

**Design reference:** `completed_designs/ve-fsbo_dashboard.html`

---

## 8.1 FSBO Overview — `/fsbo`

### 1. Page Identity & Access
- **Route:** `/fsbo`
- **Page title:** "Dashboard"
- **Allowed roles:** FSBO Customer
- **Redirect rule:** Non-FSBO roles → `/dashboard`
- **Auth requirement:** Protected + FSBO_Customer role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/dashboard/fsbo/overview` — overview data:
    - `properties[]` — FSBO-owned properties with status, missing-doc count, portal-visible message count
    - `critical_next_steps[]` — ranked action items (real, derived from missing docs/dates/tasks). Each step carries `action_kind: "upload_documents" | "open_property"` so the frontend can render per-row inline actions without parsing strings.
    - `upcoming_deadlines[]` — next ~21 days of key dates / task due dates with `consequence` text for the expandable detail.
    - `closing_timeline` — rollup for the nearest-closing property: `{closing_date, days_to_close, current_stage_label, file_status_label, address}`. Drives the "Days to closing" KPI body.
    - `missing_documents_count`
    - `share_links_live`
    - `days_to_close_nearest`
    - `recent_milestones[]`
    - `ai_guidance` — deterministic plain-English next-decision + glossary
    - `support_contact` — coordinator name/email/phone. Resolved per-tenant via `fw.resolve_support_contact`: prefers the assigned TC/Admin on the transaction, then the tenant's primary admin, then the default constant.
    - `boundary_notice`
  - Property detail page reads `GET /api/v1/dashboard/fsbo/properties/{id}` (ownership-checked). Response includes `contacts[]` (buyer / buyers_agent / title / attorney etc. with decrypted PII + call/email actions) and per-message `seen: boolean`.
  - Documents board reads `GET /api/v1/dashboard/fsbo/documents` (per-property projection).
  - Milestones page reads `GET /api/v1/dashboard/fsbo/milestones` (timeline + portal-visible coordinator messages with `seen` flag).
  - Property Detail and Milestones page mount fires `POST /api/v1/dashboard/fsbo/messages/seen` with the visible log_ids — idempotent, cross-owner-filtered, silences the unread dot on the next refetch.
- **Loading state UI:** FSBO-styled skeleton with portfolio card placeholders
- **Empty state UI:** "Welcome! Add your first property to get started." with "Add Property" CTA
- **Error state UI:** Error banner with retry

### 3. Layout & Component Hierarchy
- **Shell variant:** FSBO/Client shell (simplified sidebar)
- **Sidebar:** KPI tiles: Critical Next Steps (count), Days to Close, Share Links Live, Missing Documents
- **Sidebar navigation:** Standalone "Dashboard" link (top of sidebar, never inside a group) + **Workspace** group (My Properties, Documents, Milestones & Messages) + Settings. The Help group is intentionally absent — Ask Velvet Elves AI is the floating chat button on every page, Notifications live in the topbar bell, and Sharing is a modal opened from the sidebar-footer Share CTA, the Overview "Share links live" KPI, and the Property Detail "Manage" rail link.
- **Sidebar footer CTA:** "Share milestones" — opens the FSBO share-management modal (`FsboShareManagementModal`, owned by `FsboShareContext`). There is no `/fsbo/share` route; managing share links is a focused, quick task that lives in a modal. (FSBO is the one role whose primary CTA lives in the sidebar footer, not the topbar, per `ROLE_DASHBOARDS_DESIGN_UPDATE_PLAN.md` pattern 11.)
- **Topbar:** Brand lockup | **Portfolio status chip** (computed from `useFsboOverview`: red "Closing in Nd" when days_to_close ≤ 7, amber "Action needed · Nd missing" when missing_documents_count > 0, else green "On track" — clicks navigate to `/fsbo`) | Notification bell | User chip. No FSBO primary CTA in the topbar.
- **Persistent action banner:** A second row below the topbar surfaces `critical_next_steps[0]` across every FSBO page (not just the Overview). Two buttons: a primary "Open" / "Upload" (action depends on `action_kind`) and a `×` dismiss. Dismissal is session-scoped (`sessionStorage` keyed on `transaction_id + title`) so a new top step still surfaces; the banner is implemented by `AppLayout` and gated on `shellVariant === 'fsbo'`.
- **Page header:** The Overview is a dashboard surface and omits the page-title row per STYLE_GUIDE §16.1. Tool sub-pages (My Properties, Property Detail, Documents, Milestones & Messages, Sharing) use the canonical §15 breadcrumb-and-serif header from `FsboPortalShell`, with the breadcrumb in `[Workspace] › [Page Title]` form (Property Detail extends it: `Workspace › My Properties › {Address}`).
- **Portal tabs:** None. The sidebar is the navigation; portal tabs would duplicate it (review-corrected 2026-05-21).
- **Primary content area:**

  **Overview section:**
  - KPI strip: My Properties, Missing Documents, Share Links Live, Days to Closing.
  - Closing-timeline rollup strip directly under the KPIs: address + `Stage · {current_stage_label}` + `File · {file_status_label}` chips.
  - Hero "Next step" card (real data, `critical_next_steps[0]`) — title, body, why-it-matters, deadline, primary action ("Upload missing documents" / "Open this property") + secondary "Share milestones".
  - "Stay on track" card — secondary ranked steps from `critical_next_steps[1..5]` rendered as rows with per-row inline actions driven by each step's `action_kind`. Hidden when only one step exists.
  - "Upcoming deadlines" card — up to five rows from `upcoming_deadlines[]`; each row is click-to-expand and reveals the row-specific `consequence` text.
  - Property portfolio strip: `FsboPropertyTile` in select mode (the Overview never navigates; clicking only focuses).
  - Recent milestones activity (last 5 events).
  - AI guidance rail card: plain-English `ai_guidance.next_decision` + glossary chips.
  - Concierge upsell rail strip — the "Learn about Concierge" button opens the AI chat with a concierge-themed initial prompt (no `/settings#concierge` route exists).

  **Properties section:** (also accessible at `/fsbo/properties`)
  - Property cards, each with: address, status (Listing Prep / Under Contract), key milestones, missing docs count, "Open timeline" and "Share link" actions

  **Documents section:** (also accessible at `/fsbo/documents`)
  - Document status board: Missing | In Progress | Uploaded | Verified | Complete
  - Upload zone for new documents
  - Flag for deletion button (requests deletion review by internal team)

  **Support section:**
  - Assigned Velvet Elves support/guide contact card
  - Boundary notice: "Velvet Elves coordinates your workflow but does not act as your agent or provide legal advice."
  - Contact options: email, phone

- **Overlay/modal inventory:**
  - Share milestone modal
  - Document upload modal
  - AI Chat panel ("Ask Velvet Elves AI")

### 4. User Actions & State Transitions

**Property card "Open timeline" click:**
- Trigger: Click
- Immediate UI: Navigate to `/fsbo/properties/:id`

**Property card "Share link" click:**
- Trigger: Click
- Immediate UI: Opens Share Milestone modal
- Fields: Recipient name (optional), expiration (24h/48h/7d/30d/custom), share description
- Submit: `POST /api/v1/dashboard/fsbo/share-link` → returns shareable URL (the raw token is returned once at creation)
- Success: Copy link to clipboard; toast "Share link created"
- Side effects: Audit log; link appears in Sharing management page

**Document upload:**
- Trigger: Drag/drop or click upload zone
- Immediate UI: File upload with progress bar
- API call: `POST /api/v1/documents/upload` with file + property ID
- Success: Document appears in list with "Uploaded" status; toast "Document uploaded"
- Side effects: Notification to assigned internal coordinator; audit log

**"Flag for deletion" click:**
- Trigger: Click on a document's flag icon
- Immediate UI: Confirmation: "Request deletion? Your coordinator will review this."
- Submit: `POST /api/v1/documents/:id/flag-deletion`
- Success: Document shows "Deletion Requested" badge; toast "Deletion request submitted"
- Side effects: Notification to assigned agent/elf for approval

**AI guidance "Ask a question" (support tab or sidebar link):**
- Trigger: Click "Ask Velvet Elves AI"
- Immediate UI: Opens AI Chat panel
- Chat provides plain-English guidance, glossary-style explanations, next-step recommendations
- AI CANNOT provide legal advice, act as the customer's agent, or make workflow decisions

### 5. Conditional Rendering Logic
- **Role-based:** FSBO sees only FSBO-appropriate content. No internal workflow logic, no task editing, no internal notes.
- **State-based:**
  - Listing Prep properties: show prep milestones (disclosures, photo approval, marketing/go-live target, launch checklist)
  - Under Contract properties: show transaction milestones (Contract → EM → Inspection → … → Close)
  - Document status colors: Missing = red, In Progress = amber, Uploaded = blue, Verified = green-light, Complete = green
- **Responsive:** Single column on mobile; property strip becomes vertical stack

### 6. Navigation Flows
- **Inbound:** `/dashboard` redirect for FSBO role; login
- **Outbound:** Property detail (`/fsbo/properties/:id`), Documents, Milestones, Sharing, AI Chat
- **Deep-link:** None on overview; sub-pages support deep-links

### 7. AI Integration Points
- **AI data on page:** Plain-English next-step guidance, milestone explanations, document requirement explanations
- **AI actions:** Ask questions, get guidance, receive glossary-style explanations
- **AI guardrails:** AI CANNOT provide legal advice or act as agent; boundary notice always visible
- **AI chat panel:** Available as "Ask Velvet Elves AI" — simplified, customer-friendly interface

### 8–10. Standard patterns
- Real-time: document status updates, new messages
- Edge case: First property → onboarding-style guidance card

---

## 8.2–8.6 FSBO Sub-Pages

**`/fsbo/properties`** — Property portfolio page (list of all FSBO properties). Same layout as overview "Properties" section but full-page. Filter by status (Listing Prep / Under Contract).

**`/fsbo/properties/:id`** — Property detail: milestone timeline, key dates, documents for this property, AI guidance specific to this property, share link management.

**`/fsbo/documents`** — Document management: upload, view status, flag for deletion. Organized by property. Status board: Missing → In Progress → Uploaded → Verified → Complete.

**`/fsbo/milestones`** — Milestones & Messages: timeline of all milestones across properties with status indicators. Messages from coordinators. Plain-English explanations of each milestone.

**Sharing management — modal, not a page.** There is no `/fsbo/share` route. Share-link management is `FsboShareManagementModal`, opened via `useFsboShare().open()` from the sidebar-footer "Share milestones" CTA, the Overview "Share links live" KPI tile, and the Property Detail "Manage" rail link (which seeds `defaultPropertyId`). The modal lists active links, supports revoke, and opens the nested `ShareMilestoneModal` for create. Frontend route attempts to `/sharing` for FSBO users are redirected back to `/fsbo` in `App.tsx`.

**Ask Velvet Elves AI — floating widget, not a page.** There is no `/fsbo/ask-ai` route. The floating `FloatingAskAi` button sits on every FSBO page; clicking it opens the shared `AiChatContext` panel with an FSBO-friendly placeholder. The Property Detail and Overview "Plain-English guide" cards link to it via `aiChat.open(...)`.

**Property Detail "People involved" panel.** `/fsbo/properties/:id` includes a "People involved" rail card sourced from `transaction_parties` (decrypted via `_safe_decrypt`). Each contact carries role label, name (or company), and inline Call / Email buttons. Empty rows (no name / email / phone / company) are dropped server-side.

**Unread coordinator messages.** Property Detail and Milestones pages render a small orange dot for any message with `seen === false`. On mount, the page POSTs the visible log_ids to `/api/v1/dashboard/fsbo/messages/seen` so the dot is suppressed on the next refetch. The endpoint upserts `(log_id, user_id)` into `communication_log_views` and rejects ids that don't belong to the FSBO user's transactions.

All FSBO sub-pages follow the FSBO shell, FSBO sidebar navigation (with active state), and the same AI/notification/responsive patterns defined in §8.1.

---

# 9. Client Portal

---

> **2026-05-30 redesign — the "closing concierge" Home.** The client landing is
> now **`/client/home`** (`ClientHomePage`), a single warm, card-based concierge
> screen reconstructed from Jake's design comp and implemented per
> `CLIENT_WORKSPACE_REDESIGN_PLAN.md`. The client nav set is **Home · Timeline ·
> Documents · Payments · Agent Info** (the comp's "Next Steps" and "Updates"
> destinations are surfaced *on* Home as the Next Best Action and Recent Updates /
> Ask Velvet cards — no separate pages, no duplicate nav). The Home is fed by an
> **additive `home` block** on the same canonical `GET /api/v1/dashboard/client`
> read (no new endpoint): hero (buy/sell verb + decrypted address + phase chip +
> closing target + progress %), next best action, "what Velvet is handling",
> upcoming dates, recent updates, documents-needing-attention, and key contacts
> (agent + deal parties). "Ask Velvet" reuses the existing two-way
> `is_client_visible` thread (`/api/v1/client/messages`) — no new LLM. The four
> tool surfaces below (§9.1–§9.4) remain reachable from the new nav.

## 9.1 Client Transactions — `/client/transactions`

### 1. Page Identity & Access
- **Route:** `/client/transactions`
- **Page title:** "My Transactions"
- **Allowed roles:** Client
- **Redirect rule:** Non-client roles → `/dashboard`
- **Auth requirement:** Protected + Client role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/dashboard/client` — the **canonical client read** that feeds all
    four surfaces (transactions + per-transaction milestones/key-dates, document
    status summary, agent card). There are **no** per-surface
    `/api/v1/client/transactions` / `/client/documents` endpoints — the rebuild
    standardized on the `/dashboard/client` namespace, mirroring FSBO's
    `/dashboard/fsbo/...` decision (CLIENT_WORKSPACE_PLAN.md D3).
  - Each transaction view: address (decrypted), status, closing date, key dates,
    milestone timeline, next milestone.
- **Loading state UI:** Transaction card skeletons
- **Empty state UI:** "No transactions yet. Your agent will add you when your transaction begins."

### 3. Layout & Component Hierarchy
- **Shell variant:** Client shell (`ClientPortalShell`) — the same §15 tool shell
  as the FSBO portal: `Your Workspace › [Page]` breadcrumb, standard
  `px-3 md:px-6` gutters, boundary-notice footer.
- **Navigation:** the AppLayout sidebar ONLY (My Transactions | Documents |
  Milestones | Agent Info). There is **no** in-shell tab bar — the prior
  `_shell` tab bar duplicated the sidebar 1:1 and was removed (D1/L1).
- **Page header:** "My Transactions" title
- **Primary content area:**
  - Transaction cards: address, status pill (Active/Closed), closing date, a
    compact milestone stepper, and the next milestone in plain English.
  - Cards are **containers with explicit buttons** (View details / Documents /
    Ask a question) — never a whole-card click target (L8).
  - "View details" → an enriched inline panel: key dates, per-transaction
    Documents/Milestones links, and the two-way "Ask a question" thread.
  - No task visibility, no internal notes.

### 4. User Actions
- **"View details" button:** Expand the inline panel (dates, milestones/documents links, thread)
- **"Documents" / "Open documents":** Navigate to `/client/documents?transaction=:id`
- **"View Milestones" link:** Navigate to `/client/milestones?transaction=:id`
- **"Ask a question":** Open the expand and focus the message composer. The topbar
  "Ask your agent" CTA (`?ask=1`) opens this directly — pre-selecting the
  transaction when the client has exactly one, prompting a choice when several.
- **Messaging:** `POST /api/v1/client/messages` to ask; `GET /api/v1/client/messages?transaction_id=`
  for the thread. The thread is gated server-side by `communication_logs.is_client_visible`
  — the client's own questions plus any team reply explicitly surfaced to them;
  internal notes / AI drafts / audit rows are never returned.

### 5. Conditional Rendering Logic
- Client sees: transaction overview, key dates, milestones, documents (view/upload), agent info
- Client CANNOT see: tasks, internal notes, communication logs (internal), AI suggestions
- Upload button visible for documents (client can upload but not delete)
- "Flag for deletion" button available (sends request to agent)

### 6–10. Standard patterns
- Real-time: milestone updates, document status changes
- AI: no direct AI interaction for clients (except possible future chat)

---

## 9.2 Client Documents — `/client/documents`

- Leads with the **real** `PortalDocumentList` (the role-scoped GET /documents,
  which returns only the client's own uploads — never agent-internal files) with
  per-row "Flag for deletion". This is the single document representation; the
  old five-column hardcoded-zero status board was removed (CLIENT_WORKSPACE_PLAN.md D4).
- A **slim, real status summary** driven by `documents_summary` shows only the
  buckets that actually have documents: **In progress / Uploaded / Verified /
  Complete**. "Missing" is **not** shown for a represented client — required-doc
  tracking is the agent's responsibility on a represented deal, so a client-facing
  Missing count would be fiction.
- **Upload is a modal** (`ClientUploadModal`) launched from the page header CTA,
  collecting **transaction + document type** (+ optional label) before submit —
  not a bare on-page dropzone (L2/L3).
- Cannot delete documents directly; "Flag for deletion" sends a request to the agent.
- Cannot see the full document center (only the client's own documents).

---

## 9.3 Client Milestones — `/client/milestones`

- Per-transaction **vertical timeline** from the real milestone projection:
  status (completed / current / upcoming), plain-English descriptions, and key
  dates. Honors the `?transaction=:id` filter from the transaction cards.
- No task details visible.
- **Share milestone link:** the existing share system (`/dashboard/fsbo/share-link`)
  is gated to FSBO + internal roles and is **not client-eligible**. Rather than
  fork a parallel share path under this rebuild, the page surfaces an honest note
  to ask the agent for a shareable link. Client self-serve sharing is a separate,
  explicitly-scoped decision (CLIENT_WORKSPACE_PLAN.md §11.3).

---

## 9.4 Agent Info — `/client/agent`

- Agent BIO section: "Learn About Your Agent"
- Agent photo/avatar, name, company, bio text, contact info (phone, email)
- One-click call/email actions
- The backend resolves the **actual Agent** (by `users.role` priority:
  Agent → TC → TeamLead → Attorney), never the first non-client assignee, so a
  client never sees their TC/attorney under "Your agent" (CLIENT_WORKSPACE_PLAN.md §4.2 #8).
- Read-only informational page

---

# 10. Admin Section

---

## 10.1 User Management — `/admin/users`

### 1. Page Identity & Access
- **Route:** `/admin/users`
- **Page title:** "User Management"
- **Allowed roles:** Admin
- **Auth requirement:** Protected + Admin role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/admin/users?page=1&limit=30` — all users in tenant
  - Query params: `role`, `status` (active/inactive), `search`, `team_id`
- **Loading state UI:** User table skeleton
- **Empty state UI:** "No users yet. Invite your first team member." with "+ Invite User" CTA

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Page header:** "User Management" title + user count | "+ Invite User" button
- **Filter bar:** Role dropdown | Status toggle (Active/Inactive/All) | Team filter | Search
- **Data table:** Name | Email | Role | Team | Status (Active/Inactive) | Last Login | Actions
- **Actions column:** Edit | Deactivate/Activate | View Activity

### 4. User Actions

**"+ Invite User" click:**
- Trigger: Click
- Immediate UI: Opens Invite User modal
- Fields: Email, Role (dropdown), Team (dropdown, optional), Transaction (optional — invite to specific transaction)
- Submit: `POST /api/v1/admin/invitations`
- Success: Toast "Invitation sent to [email]"; row appears with "Invited" status
- Side effects: Email sent; audit log

**"Edit" action click:**
- Navigate to `/admin/users/:userId`

**"Deactivate" action click:**
- Trigger: Click
- Immediate UI: Confirmation dialog "Deactivate [Name]? They won't be able to log in."
- Confirm: `PATCH /api/v1/admin/users/:id` with `{ is_active: false }`
- Success: Status changes to "Inactive"; toast "User deactivated"
- Side effects: Audit log; user's JWT invalidated

### 5–10. Standard patterns

---

## 10.2 User Detail — `/admin/users/:userId`

- Full user profile: all fields editable by Admin
- Role change (with confirmation dialog and audit log)
- Team assignment/removal
- Activity log: recent actions by this user (pulled from audit_logs)
- Transaction assignments list
- Integration status (email, e-sign connected)

---

## 10.3 Task Templates — `/admin/task-templates`

### 1. Page Identity & Access
- **Route:** `/admin/task-templates`
- **Page title:** "Task Templates"
- **Allowed roles:** Admin, Team Lead
- **Auth requirement:** Protected + Admin or Team Lead role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/task-templates?scope=tenant` (Admin) or `?scope=team&team_id=:id` (Team Lead)
- **Loading state UI:** Template row skeletons

### 3. Layout & Component Hierarchy
- **Page header:** "Task Templates" title + count | "Import Templates" button | "+ Add Template" button
- **Filter bar:** Category (Welcome, Documentation, Vendor, Closing, Follow-Up, Meta) | Use Case (Buy-Fin, Buy-Cash, Sell-Fin, Sell-Cash, Both-Fin, Both-Cash) | Automation Level | Search
- **Data table:** Task Name | Category | Use Cases | Dependencies | Float | Automation | Actions
- **Actions:** Edit | Duplicate | Deactivate

### 4. User Actions

**"Edit" click:** Opens template detail at `/admin/task-templates/:id`

**"+ Add Template" click:** Opens template creation form with: Name, Description, Target, Category, Use Cases (multi-select), Dependencies (task picker), Float Days, Automation Level, Conditions (JSON builder)

**"Import Templates" click:** Navigate to `/admin/task-templates/import` — bulk import from CSV/spreadsheet

### 5. Conditional Rendering Logic
- **Admin:** sees all tenant-wide templates; can edit system-wide defaults
- **Team Lead:** sees team-specific overrides; cannot edit system-wide templates but can create team-level overrides

---

## 10.4 Task Template Detail — `/admin/task-templates/:id`

- Full template editor: all fields from task_templates schema
- Dependency rule builder: visual interface for configuring task-to-task and task-to-date dependencies
- Condition builder: JSON visual editor for wizard field conditions
- Use case checkbox matrix
- Preview: "This task will be generated for [X] transaction types"
- Save: `PATCH /api/v1/task-templates/:id`
- Side effects: Audit log; if "apply to active transactions" selected → preview of affected transactions before confirmation

---

## 10.5 Task Template Import — `/admin/task-templates/import`

- File upload (CSV/XLSX)
- Preview table showing imported tasks with validation
- Mapping interface: map CSV columns to template fields
- Conflict resolution: if template name exists, offer Skip/Override/Rename options
- Import: `POST /api/v1/task-templates/import`
- Success summary: "X templates imported, Y skipped, Z errors"

---

## 10.6 AI Confidence Settings — `/admin/confidence`

### 1. Page Identity & Access
- **Route:** `/admin/confidence`
- **Page title:** "AI Confidence Settings"
- **Allowed roles:** Admin
- **Auth requirement:** Protected + Admin role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/confidence-settings`

### 3. Layout & Component Hierarchy
- **Page header:** "AI Confidence Settings" title
- **Primary content area:**
  - Global settings card:
    - "Ship It" threshold slider (default 90%) — above this, AI auto-proceeds
    - "Review Required" threshold slider (default 75%) — below this, always requires human review
    - Global minimum floor slider — lowest allowed threshold for any team
  - Task category overrides:
    - Table: Category | Current Threshold | Risk Level | Override slider
    - Categories: signature checks (lower risk), field completion (lower), legal interpretation (higher), clause meaning (higher)
  - Team-specific overrides section (if teams exist):
    - Per-team threshold display with edit capability
    - Cannot go below global minimum floor (slider constrained)
  - Real-time validation: warnings if thresholds are set too low/high
  - Changes audit-logged

### 4. User Actions
- Slider changes: auto-save with debounce; `PATCH /api/v1/confidence-settings`
- Validation: if team lead tries to set threshold below admin minimum → blocked with message

---

## 10.7 Audit Logs — `/admin/audit-logs`

### 1. Page Identity & Access
- **Route:** `/admin/audit-logs`
- **Page title:** "Audit Logs"
- **Allowed roles:** Admin
- **Auth requirement:** Protected + Admin role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/admin/audit-logs?page=1&limit=50` — system-wide audit log
  - Query params: `user_id`, `entity_type`, `action`, `date_start`, `date_end`, `search`
- **Loading state UI:** Log row skeletons

### 3. Layout & Component Hierarchy
- **Page header:** "Audit Logs" title | "Export" button
- **Filter bar:** User filter | Entity type (transaction/task/document/user/etc.) | Action type (create/update/delete/etc.) | Date range | Search (keyword across summary text)
- **Log table:** Timestamp | User | Role | Action | Entity | Summary | Details (expandable)
- **Expandable details:** Before/after state diff, IP address, request ID
- **Pagination:** 50 per page

### 4. User Actions
- **Row expand:** Click to show before/after state diff
- **Export:** Downloads filtered logs as CSV
- **Filter changes:** Real-time table filtering (server-side for large datasets)

---

## 10.8 Tenant Settings — `/admin/tenant`

- Tenant/brokerage configuration:
  - Branding: logo upload, primary/secondary colors, custom domain
  - AI provider: OpenAI / Claude toggle with model selection
  - Feature flags: toggle features on/off
  - Data retention settings
  - Default notification policies
- Save: `PATCH /api/v1/tenants/:id`
- Side effects: Branding changes apply across all pages via CSS variables; audit log

---

# 11. Profile

---

## 11.1 Profile — `/profile`

> **⚠ Superseded (May 2026 redesign — see `ACCOUNT_MODAL_REDESIGN_PLAN.md`).** There is no standalone Profile page or route. Identity now lives as the **Profile** section inside the shared **Account modal** (opened from each role's avatar menu / footer gear). Same fields and the same `PATCH /api/v1/users/me` save path described below; the surface is a modal section rather than a page. `/profile` still 301-redirects to `/analytics?scope=me` for legacy report links.

### 1. Page Identity & Access
- **Route:** `/profile`
- **Page title:** "Profile"
- **Allowed roles:** All authenticated roles
- **Auth requirement:** Protected

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/users/me` — full user profile
  - `GET /api/v1/integrations` — connected integrations
- **Loading state UI:** Profile form skeleton

### 3. Layout & Component Hierarchy
- **Shell variant:** Role-appropriate shell
- **Page header:** "Profile" title
- **Tab bar:** Personal Info | Notifications | Checklist Templates (Agent/Team Lead only) | Integrations

**Personal Info tab:**
- Avatar upload/change
- Full name, email (read-only), phone, bio, company name
- Save button: `PATCH /api/v1/users/me`

**Notifications tab:**
- Toggle matrix: rows = notification types (task assignments, task due dates, document actions, AI email sends, communications received, deadline reminders, daily summary); columns = channels (email, push, in-app)
- Save auto-applies on toggle change

**Checklist Templates tab (Agent/Team Lead only):**
- Buyer closing checklist template editor
- Seller closing checklist template editor
- Tagged notes section (notes that get injected into printed checklists)
- Seller escrow overage reminder defaults
- Rich text editors for template content

**Integrations tab:**
- Email: Gmail / Outlook / iCloud connection status with Connect/Disconnect buttons
- E-Signature: DocuSign / HelloSign connection status
- Calendar: Google Calendar / Outlook Calendar connection status
- Each integration: status indicator (Connected/Disconnected), connected account email, Connect/Disconnect/Reconnect buttons
- Connect: initiates OAuth flow for the respective provider
- Disconnect: confirmation dialog → revokes tokens

### 4. User Actions
- Profile updates: `PATCH /api/v1/users/me`
- Integration connections: OAuth flows
- Checklist template saves: stored in `profile_settings_json`
- All changes audit-logged

### 5. Conditional Rendering Logic
- **Role-based:**
  - Agent/Team Lead: see Checklist Templates tab
  - Client: see Personal Info and Notifications only
  - FSBO: see Personal Info, Notifications, and Sharing preferences
  - Vendor: see Personal Info only

### 6–10. Standard patterns
- First-time user: if profile incomplete after first transaction upload → banner prompts for completion
- Edge case: Disconnecting email integration → warning "You won't receive automated emails. Are you sure?"

---

# 12. Shared / Public

---

## 12.1 Public Milestone Viewer — `/milestones/:shareToken`

### 1. Page Identity & Access
- **Route:** `/milestones/:shareToken`
- **Page title:** "[Client/Property] — Milestone Progress"
- **Allowed roles:** Public (no authentication required)
- **Redirect rule:** If token is invalid/expired → "This link has expired" page with suggestion to request a new one
- **Auth requirement:** Public (share token validation only)

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** Valid, non-expired share token
- **API endpoints on mount:**
  - `GET /api/v1/milestones/shared/:token` — public milestone data:
    - `property_address`, `milestone_steps[]` (name, status, date), `key_dates[]` (label, date, status)
    - NO internal notes, NO tasks, NO documents (only status cues), NO contact details (except agent name)
- **Loading state UI:** Minimal branded page with spinner
- **Error state UI:** "This link has expired or is no longer valid" with tenant branding

### 3. Layout & Component Hierarchy
- **Shell variant:** None — standalone branded page
- **Primary content area:**
  - Tenant branding header (logo, name)
  - Property address
  - Milestone timeline: visual timeline (Contract → EM → Inspection → Appraisal → CD → CTC → Close) with completed/current/upcoming indicators
  - Key dates list: closing date, possession date, other milestone dates with status colors
  - Document status cues (only): "Purchase Agreement: Complete", "Inspection Report: In Progress" — no download/view links
  - Footer: "Powered by Velvet Elves" | "Last updated: [timestamp]"
- **NO editable elements, NO task details, NO internal workflow information, NO document downloads**

### 4. User Actions
- **None** — this is a read-only view. No interactive elements beyond scrolling.

### 5. Conditional Rendering Logic
- **Token-based:** Content scope determined entirely by what the share link creator specified
- **Expired tokens:** Friendly expiry message with tenant contact info
- **Responsive:** Single-column, mobile-optimized layout

### 6. Navigation Flows
- **Inbound:** Direct URL (shared via email, text, etc.)
- **Outbound:** None (standalone page; no navigation to other app pages)

### 7. AI Integration Points
- **None** — public page has no AI features

### 8. Real-Time & Notification Behavior
- **Live updates:** None on this page
- **Viewer notification:** When someone opens this link, a notification is sent to the link creator (FSBO/Client) that their shared link was viewed
- Side effect: `POST /api/v1/milestones/shared/:token/viewed` (fires on page load)

### 9–10. Standard patterns
- Edge case: High traffic on shared link → caching for public milestone data (CDN-friendly)
- Link opened in expired state → clear message, no broken UI

---

# 13. Cross-Cutting Workflows

---

## A. New Transaction Creation Flow

### Entry Points
1. "+ New Transaction" CTA (topbar button, sidebar button — available on all internal pages)
2. Document drag-and-drop anywhere in the authenticated workspace
3. Dashboard upload intake card
4. Direct navigation to `/transactions/new`

### Quick-Create Modal (from CTA click)
**Trigger:** Click "+ New Transaction" from topbar or sidebar
**Modal contents:**
- "AI Import" action card: "Paste a contract or MLS listing — AI will auto-fill all fields"
  - Text paste area (for pasting contract text)
  - File drop/browse zone (for uploading documents)
  - On paste/drop → AI parsing begins → fields auto-populate below
- Manual entry fields (populated by AI or entered manually):
  - Client Name (required)
  - Property Address (required) + City/ZIP
  - Transaction Type: Buyer / Seller / Dual Agency (required)
  - Financing: Cash / Financed (required)
  - Purchase Price
  - Contract Date
  - Projected Closing Date
  - Lender/Title Company
  - Notes
- "Create with AI Checklist" primary button → creates transaction + generates tasks
- "Full Wizard" link → navigates to `/transactions/new` for full wizard experience

**"Create with AI Checklist" click:**
- API call: `POST /api/v1/transactions` with form data → `POST /api/v1/tasks/generate` with confirmed use case
- Success: Transaction created; tasks generated; redirect to `/transactions/active?highlight=:newId`; toast "Transaction created with X tasks"
- If first transaction: trigger profile completion prompt if checklist templates missing

### Full Wizard Flow (from `/transactions/new` or "Full Wizard" link)

**Step 1 — Document Upload:**
- Drag-drop or browse for files (PDF, JPEG, GIF, DOC, DOCX; up to 20MB per file)
- Multiple files allowed; order doesn't matter
- Auto-compression for files over 10MB
- Multi-page document splitting: preview with page range selection
- "Skip — enter details manually" link (for when no documents are available)
- Upload: `POST /api/v1/documents/upload` per file

**Step 2 — AI Parsing Progress:**
- Animated progress display: "Reading documents…" → "Extracting property data…" → "Identifying parties…" → "Checking dates…"
- Double-check mechanism: two-pass extraction with agreement check
- If passes disagree: show fields where AI is uncertain with amber highlight and "Low confidence" badge
- Show extracted data as it becomes available (streaming feel)
- Error handling: blurry docs → "Unable to read. Please upload a clearer copy or enter manually." with manual entry fallback

**Step 3 — Address Confirmation:**
- AI-normalized address displayed: Street, City, State, ZIP
- Validation: city/state/zip alignment check
- Inconsistency flags: highlighted with amber border and explanation
- User must confirm address (checkbox or "Confirm" button)
- Edit capability: all fields editable before confirmation

**Step 4 — Purchase Information Validation:**
- Display all extracted data for confirmation:
  - Final purchase price (tracked across counteroffers/amendments)
  - Contract acceptance date
  - Closing date
  - Possession date
  - Insurance days
  - Inspection days
  - Home warranty info (who orders)
  - HOA documentation days
  - Professional fees (who pays what)
  - Financing status
  - Appraisal status (cash only)
- Discrepancy flags: inconsistencies between documents highlighted with inline alerts
- Signature verification: "All documents signed by all parties" check; flag missing signatures
- Document preview panel: shows relevant document sections alongside extracted data
- User must explicitly confirm all variable dates, price, and fees
- "Suggest AI Improvement" button (optional — user feedback to improve AI)

**Step 5 — Missing Information Handling:**
- For each missing required field:
  - Prompt: "We couldn't find [field]. Please enter it below."
  - If user doesn't know: "Search" button → AI searches public sources (Google for contact info, company websites, licensed contact info)
  - Search screen: animated "Searching for [field]…" with activity indicators
  - Results: clearly labeled "AI-sourced" with source attribution
  - User must confirm any externally sourced data (explicit checkbox)
  - No auto-acceptance of external data

**Step 6 — Confirmation Page:**
- Single summary page showing all extracted/entered data:
  - Address (confirmed)
  - Purchase price
  - Closing date + closing mode (if applicable)
  - All deadline dates
  - All parties with contact info
  - Financing status
  - Appraisal status (if cash)
  - Uploaded documents list
- Edit buttons per section (edit in place; one-time validation, no rescan)
- "Accept & Create Transaction" primary button
- On confirmation only: system creates transaction → locks baseline dates → generates task list

### Post-Creation
- Redirect to `/transactions/active?highlight=:newId`
- If first transaction and profile incomplete → overlay prompt: "Complete your profile to enable closing checklists and notification preferences" with link to `/profile`
- Toast: "Transaction '[Client Name]' created with [X] tasks"

---

## B. Transaction Lifecycle Management Flow

1. **Active Transactions workspace:** View, filter, sort transactions (§4.1)
2. **Card expansion:** See tasks, key dates, contacts in 3-column drawer
3. **Inline task completion:** Checkbox in drawer or task queue
4. **Key date editing:** Inline date popover with Save/Cancel
5. **AI suggestions:** Next-step banners, drawer suggestions panel
6. **Document management:** Upload/view/email/e-sign from transaction context
7. **Transaction type switching:** If use case changes (e.g., Financing → Cash):
   - Check all task IDs for completed status → preserve completed tasks
   - Generate new tasks that didn't exist in previous use case
   - Remove/sleep tasks that don't apply to new use case (soft-delete, restorable)
   - Log all updates for audit
   - Toast: "Transaction type updated. [X] tasks added, [Y] tasks removed."
8. **Status transitions:** Active → Completed (all tasks done + closing date passed) → Closed (admin/agent marks as closed)
   - Paused: agent can pause a transaction (tasks stop generating reminders)
   - Incomplete: saved but wizard not finished
9. **Post-closing feedback:** On first view of a recently closed transaction → prompt: "How was this transaction?" with useful/unnecessary/missing task feedback options
   - Feedback stored for AI learning system
   - Compliance tasks cannot be marked as "unnecessary for all future transactions"

---

## C. Task Management Flow

1. **Auto-generation:** Upon wizard confirmation, tasks generated from confirmed use case + dates + dependency logic. No AI creativity at generation stage.
2. **Manual task creation:** "+ Add Task" modal with fields: name, completion method, due date, assign to. Before saving, AI checks for similar incomplete tasks → presents Add / Combine / Disregard.
3. **Task assignment:** Self, AI Agent, or team member. Assignment sends notification.
4. **Completion methods:** Phone Call, Email, DocuSign/E-Signature, In Person, Upload Document, Online Portal, AI Agent, Other. Completion method affects what happens on "complete" (e.g., E-Signature triggers e-sign flow).
5. **AI task intelligence:** As transaction progresses, AI recommends adding/removing tasks with transparency (reason, source, suggested deadline). Appears on AI Suggestions page and in transaction drawer.
6. **Team lead approval:** Bulk approve AI recommendations with preview of affected transactions. "Apply to all future" requires preview showing how many active transactions will be modified.
7. **Dynamic task updates on type switch:** See §B.7 above.
8. **Notification chain:** Day-before → due-today → past-due reminders. Compiled summaries: "You have 3 transactions with deadlines due tomorrow."

---

## D. Document Lifecycle Flow

1. **Upload:** Drag-and-drop anywhere in workspace, or from document center, or from wizard, or from transaction detail
2. **AI classification:** AI identifies document type, suggests name, confirms transaction, checks signature status
3. **Storage:** Supabase Storage with versioning. Vendor re-uploads create new versions; old marked as legacy.
4. **Emailing:** Select recipients (suggest transaction participants), subject (auto-filled), body (template), attachments. Send via connected email provider.
5. **E-signature flow:** Send for signature → specify recipients for executed copy → track status → receive signed → auto-replace original (old to version history) → distribute to identified parties
   - Named documents (PA, C1, Amend) → auto-sent to all parties
   - Other documents → notify responsible internal owner
6. **Client/FSBO view:** Document statuses: Missing → In Progress → Uploaded → Verified → Complete. Can upload but not delete; can flag for deletion.
7. **Vendor view:** Upload only (own documents), see own uploads. Re-upload creates new version (old = legacy). Cannot see full document center.
8. **Cross-transaction search:** All Documents workspace with AI-powered search by name, buyer, seller, keyword

---

## E. Communication & AI Email Flow

1. **Email account configuration (Milestone 4.1, prerequisite):** User connects Gmail and/or Outlook in Settings → Email Integrations (§6.3). At least one provider must be active for the AI to send replies. Tokens stored Fernet-encrypted at rest.
2. **Inbound email:** System receives via the connected provider → logged in communication log → triggers AI processing.
3. **AI determination:** AI tags the inbound with one of five `ai_kind` buckets — Factual question, Document request, Vendor reply, Uncertain — review carefully, Other — and computes a confidence percent and any flagged-assumption phrases.
4. **High confidence + factual / document exists → AI may auto-respond** (when `tenants.settings_json.ai_email.auto_send_threshold` is met; default 90%). The owner agent is CC'd so they keep a copy in Sent.
5. **Document missing, uncertain, or below threshold → AI drafts but does NOT send.** The draft lands in the AI Email Review queue (§6.4) at `/ai-emails`. Hedged phrases are wrapped in amber `<mark>` tags inside the body and listed explicitly in a "Flagged assumptions" panel.
6. **Reviewer workflow (Milestone 4.2):** open `/ai-emails`, pick a draft, verify against the AI Verified From rail (every fact the AI cited) + Original Inbound card. Then choose Approve & Send, Edit & Send (clears flagged assumptions), Regenerate, or Discard. List polls every 60 s and bell badge stays in sync.
7. **Vendor communication (Milestone 4.3):** The agent reaches the outbound template flow today by opening `/vendors/:vendorId` and clicking the **Email** button on an opted-in contact card. (A task-card "Email vendor" CTA inside the Active Transactions drawer is the intended primary entry point; the modal and hooks exist but are not yet imported by any page — tracked as a Phase 5 follow-up in [M4_3_DOC_REMEDIATION_PLAN.md §4](M4_3_DOC_REMEDIATION_PLAN.md).) `VendorRequestModal` lets them pick from the seeded constrained-format templates ("Reply with: Scheduled: YYYY-MM-DD"). `POST /vendor-communications/send` stamps the outbound row with `metadata_json.task_id`, `thread_key=VE-TASK-<short id>`, and a generated `message_id_header` so the inbound reply threads back to the right task. When the vendor replies, the engine produces both an AI draft (in the existing `/ai-emails` queue) AND a `vendor_proposals` row that links the draft to the candidate task date. The AI Email Review page shows a "Linked Task Proposal" panel in the right rail with Accept / Clarify / Reject buttons; accepting updates `tasks.due_date` and writes a `vendor_proposal_accepted` audit log. Vague replies become `needs_clarification` proposals; one click drafts a clarification email through the same engine. The standalone `/vendor-proposals` page groups pending and clarification proposals across all transactions, polling every 60 s alongside the AI Email queue.
8. **Vendor contact cards + colleague invites (Milestone 4.3):** `VendorContactCard` shows the company plus opt-in contacts; an explicit "Add colleague" CTA generates a single-use public URL (`/v/:token`) and copies it to the clipboard. The recipient lands on a tenant-branded `AddColleaguePage`, submits first/last/email/phone, and is attached as a contact to the vendor company — never to a transaction as primary. Tokens are SHA-256 hashed, TTL-bounded (default 7 days), single-use, and rate-limited. Background "Refresh info" runs surface suggestions from tenant data (matching contacts and same-name vendor records) in `BackgroundRefreshDrawer`; nothing applies without an explicit per-field accept. Phone icons render a disabled "Call via … (coming soon)" menu by default — Twilio wiring lands in Phase 6/7 and toggles on via the tenant setting `vendor_comms.phone_action_enabled`.
9. **Communication log (Milestone 4.3):** Immutable, searchable, filterable by date/party/keyword. The unified surface lives at `/admin/communications` (TeamLead/Admin gated; the legacy `/communications` URL redirects there) and groups results by date with a "Vendor traffic only" chip plus channel filter (Email today; SMS/Voice flagged as "soon"). Download: one transaction at a time per user; multi-transaction requires admin via the existing `/admin/communication-exports` flow.

---

## F. AI Chatbot Interaction Flow

1. **Floating AI chat panel:** Available throughout the workspace (all internal pages)
2. **On dashboard login:** AI offers "most important things today" briefing: overdue tasks, due-today tasks, timeline reminders
3. **Contextual:** When a transaction card is expanded, chat receives that transaction's context
4. **Quick-action prompts:** "Show overdue tasks", "Draft inspection response", "Summarize [client] deal"
5. **AI as filter/sort layer:** User asks in natural language ("show me deals closing next week"), AI filters the workspace
6. **All caught up → leisure:** If no pending actions, AI offers leisure time suggestions or prospecting tips
7. **Always available but non-intrusive:** Panel is floating, minimizable, does not overlay critical content

---

## G. Attorney Workflow

1. **Upload legal packets:** Title commitments, settlement statements, affidavits, signed amendments, recording packets
2. **AI processing:** Extract deadlines, compare versions, index exhibits, flag missing formal documents. Route anything needing legal judgment back to attorney queue.
3. **Queue filters:** All | Needs Review | Missing Docs | Ready To Release | Clean Files
4. **Matter cards:** Review queue with sign-off checkboxes (human), key dates with status colors, AI-prepared next step (labeled)
5. **AI-vs-human boundary (ABSOLUTE):** AI prepares, human decides. AI may compare, extract, index, summarize, draft. AI must NOT determine legal equivalence, final packet release, or same-day disbursement exceptions.
6. **State rules:** Closing mode, recording timelines, disbursement timing, same-day release checks
7. **Release approval:** Explicit human action with confirmation modal → writes to communication history and audit logs

---

## H. FSBO Customer Journey

1. **Entry:** FSBO-specific workspace with simplified shell
2. **Property-centric:** Listing-prep state (disclosures, photos, marketing) → Under-contract state (full milestone timeline)
3. **Document submission:** Status tracking (Missing → In Progress → Uploaded → Verified → Complete). Can flag for deletion.
4. **Milestone viewing:** Plain-English AI guidance (next step, why it matters, deadline explanations, glossary-style)
5. **Milestone sharing:** Generate expirable read-only links; viewer-open notifications
6. **Shared viewer experience:** Timeline + key dates only. No task editing, document deletion, or internal notes.
7. **Support boundary:** "Velvet Elves coordinates workflow but does not act as your agent or provide legal advice."

---

## I. Team Lead Workflow

1. **Dashboard:** Team-aggregated KPIs and intervention queue ranked by likelihood of breaking
2. **Toggle:** Personal view (own deals) ↔ Team view (all team deals)
3. **Agent board:** Drill-down into individual agent's portfolio
4. **Task templates:** Override templates for team; configure dependencies
5. **Bulk approval:** AI task recommendations with preview of affected transactions
6. **Drift/discipline monitoring:** Closings in 7 days with unresolved deps, no client touch 72+ hrs, missing signatures, agent coaching indicators

---

## J. Notification & Reminder System

1. **In-app notifications (bell icon):** Task assignments, task due dates, document actions, AI email sends, communications received
2. **Push notifications:** Browser push supported
3. **Email reminders:** Day-before, due-today, past-due. Compiled summaries: "You have 3 transactions with deadlines due tomorrow."
4. **Daily summary email:** Only when tasks are due; NOT sent when everything is clear
5. **Configurable preferences:** Per-user toggles (email/push/in-app per notification type)
6. **Escalation reminders:** Configurable 24–48 hour follow-up if no action taken
7. **SMS hooks:** Architecture-ready for future SMS integration (data model supports it, provider can be added later)

---

## K. Admin Configuration Flow

1. **User management:** Create, invite, activate/deactivate, role assignment
2. **Task templates:** Edit definitions, dependencies, float, automation flags, use-case applicability
3. **AI confidence thresholds:** Global minimum floor, per-team overrides, per-category overrides
4. **Tenant settings:** Branding (logo, colors, domain), AI provider selection (OpenAI/Claude)
5. **Audit logs:** Searchable, filterable, exportable

---

## L. Profile & Settings Flow

1. **Personal info:** Name, email, phone, bio, avatar
2. **Notification preferences:** Per-channel toggles
3. **Buyer/Seller closing checklist templates** (Agent/Team Lead)
4. **Tagged notes** for checklist printing
5. **Seller escrow overage reminder defaults**
6. **Preferred vendor list management**
7. **Email/calendar integration** connections (Gmail, Outlook, iCloud)
8. **E-signature provider** connection (DocuSign, HelloSign)
9. **First-time user overlay tutorial** (skippable, re-viewable)
10. **Post-first-transaction profile completion prompt** if required fields or checklist templates missing

---

# 14. Global Interaction Patterns

These patterns must be consistently applied across all pages.

### 1. Global Drag-and-Drop Document Intake
- Dropping a document anywhere in the authenticated workspace triggers the AI intake flow
- Flow: AI identifies document type → suggests a name → confirms which transaction → checks signature needs
- If no transaction context: AI asks user to select/confirm the transaction
- Available on all internal pages; not available on public pages or unauthenticated pages

### 2. Global Search
- Always available in topbar (all internal pages)
- Searches across: client names, vendor names, companies, dates, addresses, document names, and all transaction fields
- Results grouped by type: Transactions, Documents, Contacts, Tasks
- Click result → navigates to relevant page/entity
- AI-enhanced: understands natural language queries ("Smith closing next week" → filtered transaction results)

### 3. AI Briefing Chip
- Persistent in topbar across all internal pages
- Shows: Critical (red count) | Needs Attention (amber count) | On Track (green count)
- Click any count → navigates to `/transactions/active?filter=:status`
- Acts as a quick filter shortcut into Active Transactions workspace
- Refreshes via polling (60 seconds) or realtime subscription

### 4. "+ New Transaction" CTA
- Available from both topbar and sidebar footer on all internal pages
- Opens quick-create modal (not full wizard — quick-create is faster)
- Same modal regardless of where triggered

### 5. Print Closing Checklist
- Available from any transaction context (expanded card footer, transaction detail)
- Pulls Buyer or Seller template from user/team profile settings
- Includes tagged notes from profile
- Includes seller escrow overage reminders
- Opens browser print dialog with formatted checklist

### 6. Audit Logging
- Every user action that modifies data is logged with: user, role, timestamp, action type, before/after state, human-readable summary
- Includes: task changes, document changes, communications, AI recommendations, date changes, status changes
- Log entries are immutable (append-only)
- Viewable by Admin at `/admin/audit-logs`

### 7. Sidebar Deal-State Filters
- Clicking Active Transactions, Pending, Closed, or All Transactions in the sidebar navigates to the corresponding transaction workspace route
- Active count badges on each

### 8. AI Confidence Indicators
- Where AI-generated content appears, show confidence level visually
- Content above auto-proceed threshold (default 90%): standard display
- Content between review and auto-proceed (75%–90%): amber "Review recommended" indicator
- Content below review threshold (<75%): red "Low confidence — human review required" indicator
- Indicator styles: small badge, ring percentage, or text label depending on context

### 9. White-Label Theming
- All pages render with tenant-specific branding via CSS custom properties
- Logo in topbar and auth pages from tenant settings
- Primary/secondary colors override default tokens
- Custom domain support
- Email templates use tenant branding

### 10. Product Tour (role-aware spotlight overlay)
- Implemented in `<ProductTour />` mounted inside `AppLayout`, wrapped by `<TourProvider />`. Spotlights any element with a `data-tour="…"` anchor in the layout chrome.
- **Auto-start triggers (at most once per user, ever):**
  - Onboarding completion → `markTourPending()` writes `sessionStorage.velvet_elves_tour_pending = "1"` → `AppLayout` consumes the flag on next mount and auto-starts the tour.
  - First sign-in for a user with no recorded tour state (server-side or local).
  - The moment the tour auto-starts, a `started` state is persisted — refreshing mid-tour never relaunches it.
- **Manual restart:** Settings → Help & Tour → Start tour (internal + Attorney; also Account modal → Help & tour). Replays never clear the persisted state.
- **Step lists** (selected via `getTourSteps(role)`; every role's shell is AppLayout, so every role has a real list):
  - **Internal** (Agent, TC, Team Lead, Admin, default fallback): 20 steps — Welcome → Workspace switcher → KPI tiles → Active Transactions → Clients → My Task Queue → All Documents → Closing Calendar → Invoices & Payments → Vendor Directory → Team (Team Overview + Teams; config lives in Settings) → Intelligence (AI Suggestions, AI Email Review, Vendor Proposals, Analytics) → Oversight (Communication Audit + Audit Log) → AI briefing → Search ⌘K → Notifications → Settings & your account (topbar account menu) → +New Transaction → Ask AI FAB → Finale. Role-gated steps (switcher, Team, Oversight, payouts) auto-skip for users without those surfaces.
  - **Attorney:** 12 steps — Welcome → Matters → Releases Queue → Recording Calendar → State Rules → AI Suggestions → Upload Legal Packet → Search → Notifications → Settings & your account → Ask AI FAB → Finale.
  - **FSBO:** 9 steps — Welcome → My Properties → Documents → Payments → Messages → Share milestones CTA → Notifications → Ask AI FAB → Portal finale.
  - **Client:** 9 steps — Welcome → Home → Timeline → Documents → Payments → Agent Info → Ask-your-agent CTA → Notifications → Portal finale.
  - **Vendor:** 6 steps — Welcome → Document Requests → My Uploads → Upload document CTA → Notifications → Portal finale.
- **Visual style:** Backdrop `rgba(15,20,30,0.55)` drawn as one full-viewport SVG rect with an animated rounded-rect hole punched via an SVG mask (a giant box-shadow was culled by Chromium whenever the cutout touched a viewport edge — i.e. every sidebar target). Spotlight = 1.5 px orange ring + soft halo element + 2 s pulse ring, 8 px padding. Tooltip card 360 px wide, flat white, hairline `ve-border`, soft shadow, **no gradient strip**; sentence-case context line above a serif title; small caret pointing at the spotlight. Placement auto-flips and clamps inside the viewport. Welcome and Finale render as a centered hero card over the uniform dim.
- **Animations:** Framer Motion fades + 0.28 s ease-out tween on spotlight moves; pulse loops every 2 s. Wrapped in `MotionConfig reducedMotion="user"`. Re-measures every animation frame; auto-scrolls the target into view once per step.
- **Controls:**
  - Next (orange primary; reads **Start tour** on the welcome card and **Finish** on the last step).
  - Back (ghost, from step 2 on). Step 1 shows **Skip tour** (ghost) in its place.
  - X in the card corner dismisses (tooltip notes it's replayable from Settings).
  - Progress dots for tours ≤12 steps (backward jumps allowed, forward blocked); longer tours use a slim proportional bar. Counter reads `2 of 9`.
  - Clicking the dimmed area does nothing (a misclick must not kill the tour).
- **Keyboard:** `→` / `Enter` advance; `←` back; `Esc` dismisses. `⌘K` / `⌘L` pass through.
- **Persistence (server-first):**
  - Every exit persists: Finish → `completed`, X/Esc/Skip → `dismissed` (+ step index), auto-start → `started`. Any recorded state suppresses future auto-starts, so the tour can never nag on refresh.
  - Authoritative record: `users.profile_settings_json.product_tour` (`{status, updated_at, step}`), written via `PATCH /users/me { profile_settings }` (whitelisted key) — sticks across browsers and devices. `localStorage.velvet_elves_tour_completed:{userId}` is written synchronously first as an offline fallback. `sessionStorage.velvet_elves_tour_pending` hands off from onboarding. Legacy `velvet_elves_tutorial_completed` is auto-deleted on first read.
- **Resilience:** Steps whose target element does not exist for the role are silently skipped after a ~1.2 s grace window. While the probe is looking, the card is withheld (uniform dim only) so a step never flashes as a mislabeled centered card.
- **Accessibility:** Rendered as `role="dialog" aria-modal="true"` with title id `ve-tour-title`. Dim/ring/pulse are `aria-hidden`. Respects `prefers-reduced-motion` via MotionConfig.

---

# 15. Constraints & Rules

1. **AI assists, humans decide.** All AI actions are recommendations. No auto-changes to dates, tasks, or communications without human confirmation (except auto-send when confidence ≥ 90% threshold per tenant settings).
2. **Transparency beats automation speed.** Every AI recommendation must show reason, source, and confidence.
3. **Nothing disappears silently.** Removed tasks "sleep" (can be restored). Deleted documents are soft-deleted. Communication logs are immutable.
4. **Do not hardcode logic.** Task templates, dependencies, confidence thresholds, reminder intervals, and AI behavior must be configurable.
5. **Everything is logged.** Every action writes to audit_logs with before/after state.
6. **Compliance tasks cannot be fully removed** from all transactions.
7. **Attorney AI guardrails are absolute.** AI must NOT determine legal equivalence, legal position, final packet release approval, or same-day disbursement exceptions. These are always human-owned.
8. **FSBO boundary.** Velvet Elves coordinates workflow but does not act as the customer's agent or provide legal advice.
9. **Dashboard deep-linking.** Dashboard cards, fast filters, and AI prompts must open filtered views in Active Transactions or the relevant workspace. No dead-end pages.
10. **MVP Active Transactions is shared.** All internal roles use the same Active Transactions workspace with role-specific adaptations (not separate pages per role).

---

**End of Frontend UI Workflow Logic Specification**
