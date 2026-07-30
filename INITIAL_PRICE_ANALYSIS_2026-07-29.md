# Initial Price Analysis

Date: 2026-07-29
Author: Jan Froben
Source: `/platform/costs` (Platform Cost & Pricing console), local environment,
signed in as the platform admin `shyna.elene@minafter.com`.
Status: ANALYSIS + RECOMMENDATION. Nothing in the product was changed. The flat
fee is still `deal_fee_cents = 5000` ($50.00).

---

## 1. Recommendation in one paragraph

**Set the initial price at $29.00 per transaction, first transaction free, sold
either singly or as a 10 + 2 bundle ($290 for 12 transactions, $24.17
effective).** The cost data does not support a cost-plus price at all: the true
variable cost of running one deal is about **$2.50**, so gross margin is above
90% at any price over $25. The entire economics of this business are
fixed-infrastructure recovery, not per-deal cost. $29 clears the cost floor by
11x, recovers today's real fixed cost at **27 deals/month**, and sits at roughly
2x ListedKit's public $14.99, which is a defensible premium for a materially
broader product without making the entry point feel heavier than the competitor
before its breadth is understood.

The current $50 fee is not unprofitable (break-even 15 deals/month, the best
margin of any option modelled here). It is a positioning risk, not a cost risk:
it is 3.3x the only public competitor price, at a moment when there is no
published pricing page, no testimonials, and no case studies to justify the gap.

**One caveat that outranks the price decision:** AWS spend grew +114% month over
month ($278 in June to $596 month-to-date in July) while serving 8 active users
and zero paying customers. Cutting the pre-launch AWS footprint is worth more to
the P&L right now than any price point on this page. See §8.

---

## 2. Method and access

1. Started a fresh backend (`uvicorn app.main:app`, port 8000) and the frontend
   dev server (Vite, port 5173) against the local environment.
2. Authenticated as `shyna.elene@minafter.com` via `POST /api/v1/users/login`.
   Confirmed `is_platform_admin: true` on `/api/v1/users/me`.
3. Pulled every endpoint that backs the console (`/platform/costs/overview`,
   `/users`, `/services`, `/registry`, `/unit-economics`) across all four range
   settings the page offers (7 / 30 / 90 days / All time).
4. Rendered `/platform/costs` in headless Chrome at all four tabs and confirmed
   the on-screen figures match the API responses exactly. The numbers quoted in
   §3 are what the page actually displays, not just what the API returns.
5. Queried the underlying `ai_usage_events`, `transactions`, `credit_*`, and
   `tenants` tables directly to rebuild the per-deal figures the console reports
   as zero (§4, §5).

---

## 3. What the console reports today

### 3.1 Overview tab

Header badge: **$596.26 MTD**.

| KPI | Value |
| --- | --- |
| Month to date (blended, all sources) | **$596.26** |
| Run rate / month (MTD projected to month end) | **$637.38** |
| AI cost, measured (LLM tokens, 30d window) | **$1.12** |
| Infrastructure & services | **$631.76** |

Blended total by range:

| Range | Total | AWS | AI measured | Supabase | Managed services |
| --- | --- | --- | --- | --- | --- |
| 7 days | $147.71 | $147.48 | $0.238 | $0 | $0 |
| 30 days | $632.88 | $631.76 | $1.121 | $0 | $0 |
| 90 days | $877.76 | $873.58 | $4.177 | $0 | $0 |
| All time | $618.19 | $614.01 | $4.177 | $0 | $0 |

Cost by source is effectively **AWS 100% / AI 0%**.

Top services (30 days):

| Service | 30d | This month | Last month |
| --- | --- | --- | --- |
| Amazon RDS | $133.87 | $124.61 | $78.70 |
| Amazon ECS | $117.67 | $112.48 | $40.74 |
| Amazon ElastiCache | $87.50 | $81.50 | $51.00 |
| Amazon EC2 (Compute) | $77.61 | $72.29 | $45.21 |
| EC2 - Other (NAT/EBS/EIP) | $56.00 | $52.15 | $18.25 |
| Amazon VPC | $51.92 | $48.95 | $21.49 |
| Elastic Load Balancing | $46.06 | $43.90 | $11.44 |
| **Amazon Textract** | **$40.66** | **$40.66** | **$0.00** |
| CloudWatch | $18.07 | $16.76 | $10.80 |
| Route 53, Secrets Manager, ECR | $2.24 | $1.67 | $0.81 |
| **Total** | **$631.76** | **~$595** | **~$278** |

AI measured vs billed: **billed: not connected** (no provider admin keys).
Freshness: all four sources synced OK at 2026-07-28 21:14 UTC.

### 3.2 By user tab

56 users in the platform, **8 active**, $1.36 attributed AI cost, 397 AI calls.

| User | Tenant | Calls | Tokens | OCR pg | Cost | / deal |
| --- | --- | --- | --- | --- | --- | --- |
| Shyna Elene | Velvet Elves | 299 | 26,304 | 658 | $1.05 | — |
| Verify v2 | Verify Brokerage v2 | 35 | 160 | 69 | $0.104 | — |
| Verify v3 | Verify Brokerage v3 | 22 | 82 | 46 | $0.069 | — |
| Wizard Tester | Wizard Test Brokerage | 14 | 155 | 23 | $0.035 | — |
| Verify v1 | Verify Brokerage v1 | 12 | 82 | 23 | $0.035 | — |
| Wizard Tester B | Wizard Test Brokerage | 12 | 64 | 23 | $0.035 | — |
| UI Shot | UI Shot | 2 | 0 | 18 | $0.027 | — |
| Automation Demo | Autopilot Realty | 1 | 1,284 | 0 | $0.005 | — |
| **Background / unattributed** | — | **324** | **829,121** | **79** | **$4.23** | — |

Note that the unattributed row carries **76% of all AI spend** and every "/ deal"
cell on the page is a dash. Both facts are explained in §4.

### 3.3 Services tab

- AWS by service: as the table above.
- Supabase: "Usage metrics not connected". No cost rows.
- **Managed services registry: empty.** The page itself says "No managed
  services yet. Add SendGrid, DocuSign, domains, and the Supabase plan fee."

### 3.4 Pricing tab (verbatim)

| Measured input | Value |
| --- | --- |
| Avg AI + OCR cost / deal | **$0** |
| Median AI cost / deal | **$0** |
| Fixed monthly (infra + services) | **$592.71** |
| Deals in window | **0** |
| Active users | 8 |
| Current fee / transaction | **$50.00** |
| Revenue, cash collected (paid purchases) | $0 (30d), $14.00 all time |
| Revenue, fees consumed (usage debits) | $200.00 (30d), $300.00 all time |

Outcome as rendered: *"Each deal contributes $50.00 after its $0 variable cost.
At 0 deals/month, projected monthly profit is $-592.7148. Break-even is 12
deals/month."*

Billing settings behind it: `deal_fee_cents = 5000`, `free_intake_count = 1`,
`bundle_enabled = true`, `bundle_size = 10`, `bundle_bonus = 2`.

---

## 4. Why the worksheet cannot be used at face value

The Pricing tab's headline sentence ("each deal contributes $50.00 after its $0
variable cost") is arithmetic performed on a missing input, not a measurement. I
verified six issues against the source and the data. The first three change the
price math; the last three change how much you should trust the console's
history.

**F-1. `transaction_id` is NULL on every usage event (blocks the whole per-deal
column).**
All 721 rows in `ai_usage_events` have `transaction_id = NULL`. Because
`/unit-economics` builds `ai_by_deal` by grouping on `transaction_id`, it finds
no deals: `deals_in_window = 0`, `avg_ai_cost_per_deal = $0`,
`median_ai_cost_per_deal = $0`, `avg_ocr_cost_per_deal = $0`. Every "/ deal"
cell on the Users tab is a dash for the same reason. Phase A-3 of
`PLATFORM_COST_AND_PRICING_ANALYTICS_PLAN.md` specified a transaction id at each
feature call site; it is not landing.

**F-2. Textract is metered at the wrong rate, understating OCR by roughly 29x.**
`textract_service.py:112` hardcodes `model="detect-document-text"`, which prices
at $1.50 per 1,000 pages. But `TEXTRACT_FEATURE_TYPES=FORMS,SIGNATURES` in
`.env`, `.env.stage`, and `.env.prod`, so the code path actually taken is
`start_document_analysis` (AnalyzeDocument), which the project's own `_OCR_RATES`
table prices at $50.00 per 1,000 pages. The evidence agrees:

- Metered: 939 pages recorded as $1.4085.
- Actually billed: **Amazon Textract $40.66** in the same month (Textract was $0
  last month, so this is a clean comparison).
- Effective rate: $40.66 / 939 = **$0.0433/page**, versus the $0.0015/page being
  recorded. AWS list price for FORMS + SIGNATURES is about $0.0535/page, so the
  billed figure is in the right band and the metered one is not.

OCR is by far the largest per-deal variable cost, and it is the one the console
gets most wrong.

**F-3. The managed-services registry is empty, so "fixed monthly" is AWS-only.**
`$592.71` excludes Supabase, SendGrid, DocuSign, Google Cloud Pub/Sub, and
domains, all of which are configured and paid for (their API keys are present in
`.env`). Real fixed cost is higher than the page states. See §5.2.

**F-4. Feature attribution is not working.** 327 of 328 LLM calls are recorded
with `feature = 'other'`. The plan's own acceptance criterion for Phase A was
"zero `feature='other'` anywhere". This does not affect the total, but it means
the per-feature donut cannot tell you which capability is expensive, which is
the input you would want for a future tiering decision.

**F-5. The OpenAI rates are self-declared placeholders.** The comment above
`_MODEL_RATES` in `ai_usage.py` says the `gpt-5` entry is a placeholder "pending
confirmation against the live OpenAI price sheet". Additionally, costs are frozen
at write time, so June's rows were priced at the old $3.00/$15.00 fallback and
July's at $1.25/$10.00. The measured AI history is internally inconsistent.
Because measured AI is 0.2% of blended cost, this does not move the
recommendation, but it should be fixed before AI cost is ever quoted to a client.

**F-6. The "All time" range under-reports.** `_day_span(None, None)` in
`platform_costs.py:178` defaults to a 30-day window when `since` is absent, so
the Layer-2 blend for "All time" only counts the last 30 days of AWS. That is
why All time ($618.19) is *lower* than 90 days ($877.76). Use the 90-day range
for history until this is fixed.

---

## 5. Corrected unit economics

### 5.1 Variable cost per deal

The console reports $0. Rebuilt from the same underlying data:

**Benchmark packet.** `velvet-elves-data/testing_docs/` holds the real Honey
Creek packet (5915 E 350 N): **10 documents, 23 pages**. This is representative:
the metered OCR distribution across 393 real parses averages 2.39 pages/parse,
against 2.3 pages/document in the packet.

| Component | Basis | Cost |
| --- | --- | --- |
| OCR, intake packet | 23 pages x $0.0433/page (AWS-billed effective rate) | $1.00 |
| OCR, mid-deal documents | ~10 pages (inspection, appraisal, addenda) | $0.43 |
| LLM, packet extraction | largest measured burst 45,682 tokens at 79.5/20.5 in/out, gpt-5 rates | $0.14 |
| LLM, deal lifecycle | median burst 9,702 tokens = $0.0295, x20 sessions over 30 to 60 days | $0.59 |
| **Variable cost per deal** | | **~$2.16** |

Using AWS list price for FORMS + SIGNATURES ($0.0535/page) instead of the billed
effective rate gives $2.46. Both bounds land in the same place, which is why the
conclusion is robust to the metering defect.

**Planning figure used below: $2.50 per deal.** A stress case of $4.00 (larger
packets, more AI turns, model price increases) does not change any conclusion.

### 5.2 Fixed cost per month

| Item | Source | Monthly |
| --- | --- | --- |
| AWS, excluding Textract | Console "Fixed monthly" | $592.71 |
| Supabase Pro | Not in registry (F-3); list price | $25.00 |
| SendGrid Essentials | Not in registry; list price | $19.95 |
| DocuSign | Not in registry; business tier list price | $45.00 |
| Google Cloud (Pub/Sub) | Not in registry; estimated | $5.00 |
| Domains, amortized | Not in registry; estimated | $4.00 |
| **Corrected fixed monthly** | | **~$692** |

The four estimated lines are market list prices, not measured spend, because the
registry is empty. They are 14% of the total, so the recommendation is not
sensitive to them, but they should be entered on the Services tab so the console
stops understating fixed cost.

Payment processing is modelled separately at Stripe standard **2.9% + $0.30**.

---

## 6. Break-even and sensitivity

Contribution per deal = `fee - $2.50 variable - (2.9% x fee + $0.30)`.
Fixed = **$692/month**.

| Fee | Contribution / deal | Gross margin | Break-even (deals/mo) | Bundle 10+2 effective | Bundle break-even |
| --- | --- | --- | --- | --- | --- |
| $14.99 (ListedKit parity) | $11.76 | 83% | **59** | $12.49 | 72 |
| $19.99 | $16.61 | 87% | **42** | $16.66 | 51 |
| $24.99 | $21.47 | 90% | **32** | $20.82 | 39 |
| **$29.00 (recommended)** | **$25.36** | **91%** | **27** | **$24.17** | **33** |
| $34.99 | $31.18 | 93% | **22** | $29.16 | 27 |
| $39.99 | $36.03 | 94% | **19** | $33.33 | 23 |
| $50.00 (current) | $45.75 | 95% | **15** | $41.67 | 18 |

For contrast, the console's own Pricing tab reports break-even at $50 as **12
deals/month**. Corrected for the zero variable cost (F-1, F-2) and the missing
managed services (F-3), the real figure is **15**, and **18** if customers buy
through the bundle. The console is optimistic by 25 to 50%.

Every row is comfortably gross-margin positive. This is the central finding:
**price is not constrained by cost here.** Choosing $14.99 versus $50.00 changes
break-even volume by a factor of four, but it never makes a deal unprofitable.
The decision is therefore about market position and adoption speed.

---

## 7. The price recommendation

### $29.00 per transaction, first transaction free.

**1. It clears the cost floor by 11x.** Variable cost is $2.50. Gross margin at
$29 is 91%. Even the $4.00 stress case leaves 86%.

**2. It is priced against the only public benchmark, not against nothing.**
ListedKit publishes $14.99 per transaction, first free, no monthly fee, credits
never expire, unlimited team members (`LISTEDKIT_COMPETITIVE_ANALYSIS_AND_FEATURE_IMPROVEMENT_PLAN.md`
§32). Velvet Elves does materially more than contract-read plus timeline: full
task engine, vendor communication, client portal, e-sign, invoicing and
payments, analytics, role dashboards. About 2x their price reads as "a serious
upgrade". 3.3x, which is what $50 is, reads as "a different category" and forces
the buyer to justify the gap before they have seen the breadth. §4.5 and §6.9 of
that same analysis flag exactly this risk.

**3. Break-even is reachable in the first quarter.** 27 deals/month is roughly 7
moderately active agents at 4 deals each, or 2 to 3 small teams. At $50 the
threshold is lower (15/month), but only if buyers arrive at $50, which is the
assumption in question.

**4. It keeps the existing billing mechanics intact.** `free_intake_count = 1`
already implements first-transaction-free, matching ListedKit's strongest
acquisition hook. The 10 + 2 bundle at $29 is $290 for 12 transactions, an
effective $24.17: a visible discount that still sits above ListedKit's list
price. No code changes are needed beyond setting `deal_fee_cents = 2900`.

**5. It leaves room to move up, which $50 does not.** Raising price after proof
(testimonials, case studies, published comparison page) is a normal motion.
Cutting from $50 to $29 after launch tells the market the first price was wrong.

### On holding $50

$50 is defensible on cost and has the best margin in the table. I would keep it,
but as the **Team / Brokerage tier**, not the entry point. That matches the
packaging already proposed in §10 of the competitive analysis: Package A
(Transaction AI) competes on price simplicity, Package B (Team Operating System)
carries the higher figure. Recommended shape:

| Package | Price | Rationale |
| --- | --- | --- |
| A. Transaction AI (solo agents, TCs) | **$29 / transaction**, first free | Neutralizes ListedKit on price simplicity |
| B. Team Operating System | $50 / transaction, or a monthly base | Sells operational control, not just AI |
| C. Brokerage / white label | Negotiated | Where per-intake pricing feels too lightweight |

---

## 8. The finding that outranks the price decision

AWS is the entire cost base (100% of blended spend) and it is growing fast:

- June: about **$278**
- July month-to-date: about **$596** (+114%)
- Run rate: **$637/month**

This is being spent to serve **8 active users, 26 transactions, and $14.00 of
lifetime collected revenue**. The shape of the bill is a production-grade
always-on footprint under near-zero load: RDS $133.87, ECS $117.67, ElastiCache
$87.50, EC2 $77.61, "EC2 - Other" $56.00 (typically NAT Gateway, EBS, elastic
IPs), VPC $51.92, ELB $46.06.

Halving the pre-launch footprint would drop break-even at $29 from 27 to about
14 deals/month, which is a larger effect on the P&L than any price point in §6.
Concretely worth reviewing before launch: whether ElastiCache is needed yet,
whether dev/stage need separate always-on RDS and NAT gateways, and whether ECS
task counts and sizes match actual load. I have not made any of these changes;
they need Jake's call on what stage and prod must keep running.

---

## 9. Required fixes before this console can be quoted to a client

Ordered by impact on the numbers.

1. **F-2, Textract rate.** Pass the actual feature set to `record_ai_usage` in
   `textract_service.py` instead of the hardcoded `"detect-document-text"`, and
   price `analyze-document` from the current AWS sheet. Today OCR is understated
   about 29x. (Small change, largest correction.)
2. **F-1, transaction attribution.** Land `transaction_id` in the usage scope so
   the per-deal column stops being empty. Without it the Pricing tab cannot do
   its one job.
3. **F-3, managed-services registry.** Enter Supabase, SendGrid, DocuSign,
   Google Cloud, and domains on the Services tab. Two clicks and one number
   each; it is the only data entry the console asks for.
4. **F-6, All-time range.** Make `_day_span` cover the full history when `since`
   is absent, so "All time" stops reporting less than "90 days".
5. **F-4, feature slugs.** Fix the call-site scopes so the feature breakdown
   works. Needed before any per-feature tiering decision.
6. **F-5, OpenAI rates.** Replace the placeholder `gpt-5` entry with confirmed
   list prices, and note in the UI that historical rows are frozen at the rate in
   force when they were written.

After 1 to 3, re-open the Pricing tab and confirm it reproduces roughly $2.50
variable per deal and about $692 fixed. If it does, the worksheet becomes
self-serve and this document stops being necessary.

---

## 10. Assumptions and caveats

- **The AI and deal-volume data is test activity, not customer load.** 26
  transactions, 8 active users, $14.00 lifetime cash collected. Per-deal *unit*
  costs derived from it are sound because they are rates (per page, per token).
  Per-month *volume* figures from it are not predictive.
- **AWS spend covers the whole account** (dev, stage, prod), while
  `ai_usage_events` covers only this Supabase project. So $0.0433/page may
  slightly overstate the per-page rate if stage or prod ran Textract pages that
  are not in this database. The AWS list-price cross-check ($0.0535/page) bounds
  it from the other side, and both land near $1.00 to $1.23 for a 23-page
  packet, so the conclusion holds either way.
- **Four fixed-cost lines are list prices, not measured spend** (Supabase,
  SendGrid, DocuSign, Google Cloud, domains), because the registry is empty.
  They total about $99 of a $692 base.
- **Stripe fees are modelled at standard 2.9% + $0.30** and are not currently
  ingested as a cost source (open item J-3 in the console plan).
- **No support, sales, or engineering cost is included.** This is
  infrastructure-only break-even. A real P&L threshold is higher.
- **Pricing is Jake's decision.** This document models it from measured cost and
  the one public competitor price; it changes nothing. Per the console's own
  guardrail: this worksheet models a price, it does not change billing.
