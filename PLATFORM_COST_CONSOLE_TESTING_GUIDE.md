# Platform Cost & Pricing Console — Testing Guide

Companion to PLATFORM_COST_AND_PRICING_ANALYTICS_PLAN.md. This is the
frontend-only, mouse-first validation script for the console that shipped as
`/platform/costs`. It follows the plan's §9 exactly, with the real component
names and the one setup step the build requires.

Everything below is validated through the UI. Typing is limited to a search
word and one number.

---

## 0. One-time setup (Jan)

The console adds columns, two tables, and one SQL function. Per project
convention Jan applies migrations; the code assumes nothing was pre-applied.

1. Apply the two additive migrations (both guarded with IF NOT EXISTS):
   - `20260910090000_platform_cost_console.sql` — user_id/quantity/unit on
     `ai_usage_events`, plus `service_cost_daily` and `service_cost_entries`.
   - `20260910091000_platform_cost_rpcs.sql` — the `cost_usage_by_user`
     aggregation function.
2. Restart the backend so the new `.env` keys and startup drift-warning load
   (dev uvicorn does NOT hot-reload `.env`).
3. Confirm you have one **platform-admin** login and one ordinary
   **tenant-admin** login on the dev stack.

Optional, for fuller data (the console degrades honestly without them):
- AWS: no key needed — Cost Explorer uses the existing dev AWS credentials
  (verified working). It needs the `ce:GetCostAndUsage` IAM action on that
  principal.
- `SUPABASE_MGMT_ACCESS_TOKEN` + `SUPABASE_PROJECT_REF` for Supabase usage
  meters (otherwise "usage metrics not connected", which is correct).
- `OPENAI_ADMIN_API_KEY` / `ANTHROPIC_ADMIN_API_KEY` for the billed-cost
  reconciliation gauge (otherwise "billed: not connected").

If the migrations are not applied, the console's endpoints error rather than
showing empty states — that is expected, and is the signal that step 1 is
outstanding.

---

## Positive path (mouse only)

1. **Sign in as the platform admin.** In the left sidebar, confirm the
   **Platform** group now shows **Tenants · AI usage · Costs & pricing · Help
   center**. The new item has a green dollar-circle icon.

2. **Open "Costs & pricing".** The **Overview** tab loads. If no costs have
   synced yet you see an honest empty card with a **Sync now** button (no fake
   numbers). The header shows a month-to-date badge once data exists.

3. **Press "Sync now"** (in the empty state, or in the freshness footer). Watch
   the footer update to "AWS synced just now" and the AWS numbers fill the
   tiles, the stacked daily chart, and the "Top services" bars. The AWS figures
   should match the AWS console's Cost Explorer for the same days (Jan verifies
   once; testers just confirm real dollar amounts appear). Textract appears as
   an AWS service line — that is correct, it is billed by AWS.

4. **Switch the range control** (7 / 30 / 90 / All time, top-right). Confirm
   every chart redraws with no errors and the month-to-date badge stays put.

5. **Open the Users tab.** Confirm you see yourself and other users, with Calls,
   Tokens, OCR pages, Cost, and Cost/deal columns. Zero-usage users appear too,
   shown with dashes rather than fake zeros. Type part of a user's name (or
   tenant) in the search box — the table filters. Try the Cost / Calls / Recent
   sort control.

6. **Real-time check.** In a second browser tab, run any AI action as a normal
   user — upload a contract through the wizard, or ask the in-app AI chat a
   question. Come back to the Users tab and press **Refresh**. Confirm that
   user's calls and cost increased. (The caption reads "Live: aggregated from AI
   events at load time.")

7. **Click the user's row.** The detail modal opens with a KPI row, a cost-by-
   feature donut, a daily trend, a per-deal cost list, and a billing-context
   footer (plan, wallet, deals billed). Confirm the modal has exactly one close
   button. Press **CSV** on the Users tab and confirm a file downloads.

8. **Open the Services tab.** Confirm AWS services are listed with costs and a
   "this month vs last" comparison. Press **Add service cost**, click the
   **SendGrid** preset chip, enter a monthly amount (e.g. `19.95`), pick a
   date, and Save. Confirm it appears in the Managed services table and, after
   a moment, is folded into the Overview blend (the "Managed services" band and
   the total). Delete it with the trash icon — confirm it asks for confirmation
   first, then disappears.
   - Bonus: try adding a service literally named "AWS" — you should get a
     "that cost may already be counted" heads-up toast (it still saves).

9. **Open the Pricing tab.** Confirm the measured numbers are filled in from
   real usage (avg AI+OCR cost per deal, fixed monthly, current fee, both
   revenue figures). Move the **Fee per transaction** slider and the
   **Projected deals / month** slider. Confirm the margin, monthly profit, and
   break-even sentences update instantly and the sensitivity table (fee −10% /
   fee / fee +10%) recomputes. Drag the fee below the variable-cost line and
   confirm it says plainly that the fee "loses money on every deal" instead of
   printing a negative break-even.

---

## Negative path (permissions)

- **N-1.** Sign in as the **tenant admin** (not a platform admin). Confirm the
  **Platform** group is absent from the sidebar entirely.

- **N-2.** While signed in as the tenant admin, paste `/platform/costs` into the
  address bar. Confirm a 404 page — not an error, and not any data. (The route
  lives inside `PlatformAdminGuard`, and every `/platform/costs/*` endpoint is
  gated by `require_platform_admin`.)

- **N-3.** (Optional, dev-only) Set `VE_COST_CONSOLE_V1=false` in the backend
  `.env` and restart. Confirm the nav item disappears and `/platform/costs`
  404s even for the platform admin — the feature flag is the kill switch.

---

## What "done" looks like

- Every capability above is reachable and correct through the UI, by a non-
  developer, with a mouse.
- The blended total counts each dollar once: Textract shows under AWS, never
  double-counted from the per-deal OCR metering; measured AI is its own band.
- The negative path proves a tenant admin can neither see nor reach any of it.

## Automated coverage already in place

- Backend: `app/tests/test_platform_costs.py` covers the permission gate
  (403 tenant-admin), the D-7 no-double-count blend (Textract counted once),
  registry CRUD, and the fixed-cost exclusion in unit-economics. Attribution
  and rate-table math are covered in `app/tests/test_ai_usage.py`.
- Frontend: the console typechecks clean under `tsc -p tsconfig.app.json`.
