# Velvet Elves — Frontend UI Workflow Logic Specification

**Version:** 1.0
**Date:** 2026-04-06
**Scope:** Complete page-by-page frontend workflow logic for all routes
**Reference Designs:** 10 approved HTML designs in `completed_designs/`
**Status:** Pre-Phase 3 design review — covers all routes through MVP

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

- **Topbar (58px):** Brand lockup + AI indicator | "Today's AI Briefing" chip (Critical / Needs Attention / On Track counts — clickable as filter shortcuts) | Global search input | Notification bell | User avatar chip | Contextual CTA (e.g., "+ New Transaction")
- **Left Sidebar (220px, dark navy `#1E3356`):**
  - 2×2 KPI tiles (role-specific; default for Agent: Overdue Tasks, Closing This Week, Active Deals, Pipeline Value)
  - Navigation groups:
    - **Dashboard** — role-specific landing
    - **Deals** — Active Transactions (badge), Pending (badge), Closed, All Transactions
    - **Workflow** — My Task Queue (badge), All Documents, Closing Calendar
    - **Intelligence** — AI Suggestions (badge), Analytics, Settings
    - **Team** (Team Lead only) — Agents, Task Templates
  - Footer: Pinned "+ New Transaction" CTA button | User profile card (avatar, name, role)
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

### 1. Page Identity & Access
- **Route:** `/onboarding`
- **Page title:** "Welcome to Velvet Elves"
- **Allowed roles:** All authenticated roles where `onboarding_completed === false`
- **Redirect rule:** If `onboarding_completed === true` → `/dashboard`. If unauthenticated → `/login`
- **Auth requirement:** Protected

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** User authenticated, `onboarding_completed === false`
- **API endpoints on mount:**
  - `GET /api/v1/users/me` — current user profile
  - `GET /api/v1/tenants/:id` — tenant settings
- **Loading state UI:** Full-page skeleton with progress bar at top
- **Empty state UI:** N/A
- **Error state UI:** Error toast + retry button

### 3. Layout & Component Hierarchy
- **Shell variant:** Standalone full-page with progress stepper (no sidebar or topbar)
- **Primary content area:** Multi-step wizard with progress indicator at top

**Steps vary by role:**

**Agent / Elf / Team Lead:**
1. **Welcome** — "Welcome, [Name]! Let's set up your workspace." Brief overview of what the platform does.
2. **Profile Basics** — Avatar upload, phone number confirmation, bio (optional for agents), company name
3. **Email Connection** — Connect Gmail / Outlook / iCloud for email integration; "Skip for now" option
4. **E-Signature Setup** — Connect DocuSign / HelloSign; "Skip for now" option
5. **Notification Preferences** — Toggle email/push/in-app notifications for: task reminders, document actions, AI emails, deadline alerts
6. **Checklist Templates** (Agent/Team Lead only) — Set up Buyer and Seller closing checklist templates or use defaults; tagged note section; seller escrow overage reminder defaults
7. **Complete** — "You're all set!" with "Go to Dashboard" CTA

**Attorney:**
1. Welcome
2. Profile Basics (name, phone, firm name, bar number via metadata)
3. State Rules Configuration — Select states of practice, confirm recording/disbursement defaults
4. Email Connection
5. Notification Preferences
6. Complete

**Client:**
1. Welcome — "Your agent [Name] has added you to a transaction"
2. Profile Basics — Name confirmation, phone
3. Notification Preferences — Simplified (email on/off, milestone updates on/off)
4. Complete

**FSBO Customer:**
1. Welcome — "Welcome to Velvet Elves! We'll help coordinate your sale."
2. Profile Basics — Name, phone, email confirmation
3. Notification Preferences
4. Complete

**Vendor:**
1. Welcome — "You've been invited to a transaction"
2. Profile Basics — Company name, name, phone, email
3. Complete

**Admin:**
1. Welcome
2. Profile Basics
3. Tenant Configuration — Logo, brand colors, domain (if first admin)
4. AI Provider Selection — OpenAI / Claude toggle with current model display
5. Notification Preferences
6. Complete

### 4. User Actions & State Transitions

**"Next" / "Continue" button (each step):**
- Trigger: Click
- Immediate UI: Validate current step fields; if valid, animate slide to next step; progress bar advances
- API call: `PATCH /api/v1/users/me` with step-specific payload (saves incrementally)
- Success: Advance to next step
- Failure: Inline validation errors; do not advance
- Side effects: Audit log for profile updates

**"Skip" links (email/e-sign steps):**
- Trigger: Click
- Immediate UI: Advance to next step without saving that integration
- No API call needed; user can configure later in Profile settings

**"Go to Dashboard" (final step):**
- Trigger: Click
- API call: `PATCH /api/v1/users/me` with `{ onboarding_completed: true }`
- Success: Redirect to `/dashboard`
- Side effects: Audit log; `onboarding_completed` flag set

### 5. Conditional Rendering Logic
- **Role-based visibility:** Steps 6 (Checklist Templates) only for Agent/Team Lead. State Rules only for Attorney. Tenant Configuration only for first Admin of a tenant.
- **State-based visibility:** If email already connected (e.g., via OAuth login), skip email step or show "Connected" state
- **Responsive behavior:** Single-column centered layout; stepper collapses to numbered dots on mobile

### 6. Navigation Flows
- **Inbound routes:** `/login` redirect (after first login), `/auth/callback` redirect, `/invite/:token` flow
- **Outbound routes:** `/dashboard` (on completion)
- **Deep-link support:** None — always starts at step 1 (progress saved, resumes at last incomplete step)
- **Back navigation:** "Back" button between steps; browser back returns to previous step. Leaving onboarding preserves progress for next visit.

### 7. AI Integration Points
- **AI data on page:** None during onboarding
- **AI actions available:** None
- **AI chat panel:** Not available during onboarding

### 8. Real-Time & Notification Behavior
- **Live updates:** None
- **Notification triggers:** None
- **Toast/alert patterns:** Validation errors inline; success toasts for integration connections

### 9. Cross-Page Relationships
- **Shared state:** User profile data populated here flows to all dashboard and workspace pages
- **Data dependencies:** Checklist templates created here are used by "Print Checklist" throughout the app

### 10. Edge Cases
- **Browser refresh mid-wizard:** Resumes at last saved step (each step auto-saves on "Next")
- **OAuth email already connected:** Show "Connected to Gmail" success state instead of connect prompt
- **First admin of tenant:** Extra tenant configuration step appears
- **User skips all optional steps:** Allowed — they can configure later from `/profile`

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
  - Vendor → `/client/documents` (vendor-scoped view)
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
  - Row 3: Primary contact (name, role) with one-click phone and email icons | Milestone bar: Contract → EM → Inspection → Appraisal → CD Delivered → CTC → Close (filled steps = green, current = amber, future = gray, overdue = red)
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
  - AI Suggestions panel: "AI Suggestions for this deal" with 2–3 contextual suggestions (e.g., "Draft inspection response", "Summarize lender email thread", "Generate repair credit counter-offer") — each with an action button
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
- Immediate UI: Card expands with slide-down animation showing 3-column drawer; other expanded cards collapse (accordion behavior)
- API call: `GET /api/v1/transactions/:id/detail` (tasks, key dates, contacts, AI suggestions) — lazy loaded on first expand
- Success: Drawer populates with data
- Failure: Drawer shows error placeholder with retry

**AI next-step CTA button click (e.g., "Send Response"):**
- Trigger: Click
- Immediate UI: Opens AI Chat panel with pre-filled action context (e.g., drafts an inspection response for review)
- API call: `POST /api/v1/ai/action` with `{ transaction_id, action: 'draft_inspection_response' }`
- Success: AI chat panel opens with draft content for user review
- Failure: Toast; panel opens with error "Unable to generate draft"

**Task checkbox click (complete task):**
- Trigger: Click checkbox in task list
- Immediate UI: Optimistic update — checkbox fills, task text strikes through, moves to "Completed" group
- API call: `PATCH /api/v1/tasks/:id` with `{ status: 'Completed', completed_at: now() }`
- Success: Task confirmed completed; info badge updates; milestone bar may advance; stage pill may recalculate
- Failure: Rollback — checkbox unchecks, task returns to previous group; error toast
- Side effects: Audit log; notification to transaction participants; task-dependent tasks may become unblocked

**"+ Add Task" click:**
- Trigger: Click
- Immediate UI: Opens Add Task modal
- Modal fields: Task Name, Completion Method (Phone Call | Email | DocuSign/E-Signature | In Person | Upload Document | Online Portal | AI Agent | Other), Due Date, Assign To (self | AI Agent | team members dropdown)
- "Get AI Suggestions on How to Complete This Task" button → expandable AI Suggested Approaches section
- On submit: API call `POST /api/v1/tasks` → before saving, AI checks for similar incomplete tasks → presents Add / Combine / Disregard choice if match found
- Success: Task appears in task list; modal closes; toast "Task added"
- Failure: Validation errors in modal; API error toast

**Key date pencil-edit click:**
- Trigger: Click pencil icon next to a date
- Immediate UI: Inline popover appears with date picker, current value pre-filled
- Popover has Save and Cancel buttons
- Save click: API call `PATCH /api/v1/transactions/:id/dates` with `{ field: 'inspection_response_date', value: '2026-04-15' }`
- Success: Date updates in place; popover closes; if date moved, dependent tasks may recalculate (toast if tasks affected: "3 task deadlines adjusted")
- Failure: Error toast; popover stays open
- Cancel click: Popover closes, no changes
- Side effects: Audit log with before/after state; dependent task recalculation; notifications if closing date changed

**Contact phone icon click:**
- Trigger: Click phone icon
- Immediate UI: Initiates `tel:` link (opens phone dialer on mobile, may open calling app on desktop)
- Future: Click-to-call/call-bridge integration

**Contact email icon click:**
- Trigger: Click email icon
- Immediate UI: Opens email compose (either in-app compose if email connected, or `mailto:` fallback)

**"Add [role]" contact link click:**
- Trigger: Click "Add title company" link
- Immediate UI: Opens Add Contact inline modal
- Fields: Company Name, First Name, Last Name, Phone Number, Email Address
- Submit: `POST /api/v1/transactions/:id/parties` with contact data
- Success: Contact appears in contacts column; modal closes
- Side effects: Contact also added to centralized contact directory for reuse

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
  - AI next-step banner: only shown if AI has a recommendation for this transaction
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
- **Page header:** "Closed Transactions" title + count pill | "Export CSV" action
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
- **Page header:** "All Transactions" title + count pill | "Export CSV"
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
- **Shell variant:** Standalone wizard (minimal shell — logo + step indicator only, no sidebar)
- **Primary content area:** Multi-step wizard — see Cross-Cutting Workflow A for complete specification
- **Steps:**
  1. Document Upload — drag/drop or browse
  2. AI Parsing Progress — show what AI is extracting with animated progress
  3. Address Confirmation — AI-normalized address with edit capability
  4. Purchase Information Validation — dates, price, fees, party data with discrepancy flags
  5. Missing Information Handling — prompts for missing data with AI search option
  6. Confirmation Page — full summary with edit/accept

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
- **Shell variant:** Internal shell (or Client/FSBO shell for those roles)
- **Sidebar state:** Parent "Active Transactions" or "All Transactions" highlighted
- **Page header:**
  - Breadcrumb: Transactions > [Client Name]
  - Title: Client name + address
  - Status pill + "why" badges
  - Milestone bar
  - Action buttons: Edit Transaction | Print Checklist | Export
- **Tab bar:** Overview | Tasks | Documents | Parties | Communications
- **Primary content area (per tab):**

  **Overview Tab:**
  - Transaction summary card: type, purchase price, financing, closing date/time, possession date/time, closing mode, status, notes
  - Key dates card (editable, same as Active Transactions drawer)
  - Recent activity timeline (last 10 events)
  - AI suggestions card

  **Tasks Tab:**
  - Full task list grouped by status: Overdue | Upcoming | Completed | Blocked | Skipped
  - Each task: name, description, due date, assigned to, completion method, status, AI confidence (if AI-recommended)
  - Actions: Complete (checkbox), Edit (pencil), Delete (trash, soft-delete), Add Task
  - Task dependency visualization (optional Gantt or tree view)
  - "Sleeping" tasks section (soft-deleted, can restore)

  **Documents Tab:**
  - Document list with: name, type, upload date, uploaded by, version, status (pending/processed/signed), signature status
  - Actions: Upload, Download, Email, Send for E-Signature, Rename, View Version History, Delete (soft)
  - Drag-drop upload zone
  - AI document search within this transaction

  **Parties Tab:**
  - Grouped contact cards by role: Buyer(s), Seller(s), Agents, Lender, Title, Attorney, Inspector, Appraiser, Home Warranty, Other
  - Each card: name, company, email, phone with one-click actions
  - Add/edit/remove contacts
  - Vendor contact card feature: outbound emails include link for vendors to add additional contacts

  **Communications Tab:**
  - Immutable communication log: all emails, system messages, document actions, AI sends
  - Each entry: timestamp, sender, direction, subject, preview
  - Search bar for filtering by keyword
  - Filter by: date range, party, channel (email/system/AI)
  - "Resend" icon on email entries (one-click resend)
  - AI draft review entries with "Approve / Edit & Send" buttons (if pending)

- **Overlay/modal inventory:**
  - Edit Transaction modal
  - Add Task modal
  - Add Contact modal
  - Document upload/email/e-sign modals
  - AI Chat panel
  - Print Checklist

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
- **Page header:** "My Task Queue" title + total count pill | "Export" action
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
  - Breadcrumb: My Task Queue > [Task Name] (or Transaction > Tasks > [Task Name])
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
- **Page header:** "Closing Calendar" title | Month/Year selector + navigation arrows (< Month >) | View toggle: Month | Week | List
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
- **Page header:** "All Documents" title + count pill | "Upload" button | "Export" button
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
- **Page header:** "AI Suggestions" title + pending count pill
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
- **Page header:** "Analytics" title | Period selector (This Month | This Quarter | This Year | Custom Range) | Export button
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

### 1. Page Identity & Access
- **Route:** `/settings`
- **Page title:** "Settings"
- **Allowed roles:** All authenticated internal roles
- **Redirect rule:** Routes to user-appropriate settings. Admin sees system settings; others see personal settings.
- **Auth requirement:** Protected

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/users/me` — current user settings
  - `GET /api/v1/tenants/:id/settings` (Admin only) — tenant settings
  - `GET /api/v1/confidence-settings` (Admin/Team Lead) — confidence thresholds
- **Loading state UI:** Settings form skeletons

### 3. Layout & Component Hierarchy
- **Shell variant:** Internal shell
- **Sidebar state:** "Settings" nav link active
- **Page header:** "Settings" title
- **Primary content area — tabbed settings:**

  **For all roles — Personal Settings tab:**
  - Notification preferences (email/push/in-app toggles per category)
  - Display preferences (date format, timezone)
  - Connected integrations status (email, e-sign, calendar)

  **For Agent/Team Lead — Workspace Settings tab:**
  - Default sort preferences
  - AI chat preferences (auto-open, context scope)

  **For Team Lead — Team Settings tab:**
  - Team-wide confidence thresholds (above admin minimum)
  - Default task template override settings
  - Team notification policies

  **For Admin — System Settings tab:**
  - AI provider selection (OpenAI / Claude toggle) with current model display
  - Global confidence floor setting
  - Tenant branding (logo, colors, domain)
  - Feature flags
  - Data retention settings

### 4. User Actions
- Toggle/dropdown changes auto-save with debounce (no explicit Save button per field)
- AI provider switch (Admin): Confirmation dialog "Switch AI provider to [Claude]? This affects all AI features."
  - `PATCH /api/v1/tenants/:id` with updated `settings_json.ai_provider`
  - Success: Toast "AI provider updated"; audit log

### 5–10. Standard patterns
- Role-based tab visibility
- Deep-link: `?tab=team` or `?tab=system`

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
  - `GET /api/v1/fsbo/dashboard` — overview data:
    - `properties[]` — FSBO-owned properties with status
    - `critical_next_steps[]` — ranked action items
    - `missing_documents_count`
    - `active_share_links_count`
    - `days_to_close` (nearest property)
    - `recent_messages[]`
  - `GET /api/v1/fsbo/notifications`
- **Loading state UI:** FSBO-styled skeleton with portfolio card placeholders
- **Empty state UI:** "Welcome! Add your first property to get started." with "Add Property" CTA
- **Error state UI:** Error banner with retry

### 3. Layout & Component Hierarchy
- **Shell variant:** FSBO/Client shell (simplified sidebar)
- **Sidebar:** KPI tiles: Critical Next Steps (count), Days to Close, Share Links Live, Missing Documents
- **Sidebar navigation:** Dashboard | My Properties | Documents | Milestones & Messages | Ask Velvet Elves AI | Notifications | Sharing
- **Topbar:** Brand lockup | "Share milestones" CTA | Notification bell | User chip
- **Page header:** "Dashboard" title
- **Portal tabs:** Overview | Properties | Documents | Support (with count badges)
- **Primary content area:**

  **Overview section:**
  - Welcome card with next decision in plain English: "Your next step is to [action]. Here's why it matters: [explanation]. Deadline: [date]."
  - Property portfolio strip: horizontal scroll of property cards (address, status pill, portfolio chips for closing date/missing docs/new messages, quick actions)
  - Recent milestones activity (last 5 events)
  - AI guidance card: plain-English summary of current status and recommendations

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
- Submit: `POST /api/v1/fsbo/share-links` → returns shareable URL
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

**`/fsbo/share`** — Sharing management: view all active share links, create new ones, revoke existing ones. Shows viewer-open notifications (who viewed when).

**`/fsbo/ask-ai`** — Full-page AI chat interface: "Ask Velvet Elves AI" — plain-English questions about the process, document requirements, timelines. Simplified interface. Cannot execute workflow actions.

All FSBO sub-pages follow the FSBO shell, FSBO sidebar navigation (with active state), and the same AI/notification/responsive patterns defined in §8.1.

---

# 9. Client Portal

---

## 9.1 Client Transactions — `/client/transactions`

### 1. Page Identity & Access
- **Route:** `/client/transactions`
- **Page title:** "My Transactions"
- **Allowed roles:** Client
- **Redirect rule:** Non-client roles → `/dashboard`
- **Auth requirement:** Protected + Client role

### 2. Entry Conditions & Data Loading
- **API endpoints on mount:**
  - `GET /api/v1/client/transactions` — transactions where this user is a party
  - Each: transaction summary (address, status, closing date, agent name)
- **Loading state UI:** Transaction card skeletons
- **Empty state UI:** "No transactions yet. Your agent will add you when your transaction begins."

### 3. Layout & Component Hierarchy
- **Shell variant:** Client shell (simplified)
- **Sidebar:** My Transactions | Documents | Milestones | Agent Info
- **Page header:** "My Transactions" title
- **Primary content area:**
  - Transaction cards: address, status pill (Active/Closed), closing date, agent name/avatar
  - Milestone bar per transaction (simplified: major milestones only)
  - Click card → expanded view showing key dates, next milestone, recent updates
  - No task visibility, no internal notes

### 4. User Actions
- **Card click:** Expand to see details (dates, milestones, documents link)
- **"View Documents" link:** Navigate to `/client/documents?transaction=:id`
- **"View Milestones" link:** Navigate to `/client/milestones?transaction=:id`

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

- Document list for client's transactions (view, download, upload)
- Status indicators: Missing, In Progress, Uploaded, Verified, Complete
- Upload zone for new documents
- "Flag for deletion" for documents client wants removed
- Cannot delete documents directly
- Cannot see full document center (only documents shared with client role)

---

## 9.3 Client Milestones — `/client/milestones`

- Timeline view of transaction milestones
- Plain-English descriptions of each milestone
- Status indicators (completed/current/upcoming)
- Key dates displayed
- Share milestone link option (generates read-only shareable URL)
- No task details visible

---

## 9.4 Agent Info — `/client/agent`

- Agent BIO section: "Learn About Your Agent"
- Agent photo, name, company, bio text, contact info (phone, email)
- One-click call/email actions
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

1. **Inbound email:** System receives via connected email provider → logged in communication log → triggers AI processing
2. **AI determination:** Is it a factual question (closing date, status), a document request, or uncertain?
3. **Factual / document exists → AI auto-responds:** CC responsible internal owner (agent + elf). Only when confidence ≥ auto-proceed threshold (default 90%).
4. **Document missing or uncertain → AI drafts but does NOT send:** Routes to human with "Approve / Edit & Send" button. All assumptions/inferences/interpretations bolded in draft.
5. **Side-by-side review UI:** Left panel = draft with bolded assumptions; Right panel = source data with tooltips showing where each piece of information came from.
6. **Vendor communication:** Constrained response format → AI parses reply → proposes date update → validates against timeline constraints. Vague replies ("soon") → AI sends clarification or routes to human.
7. **Communication log:** Immutable, searchable, filterable by date/party/keyword. Download: one transaction at a time per user; multi-transaction requires admin.

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
