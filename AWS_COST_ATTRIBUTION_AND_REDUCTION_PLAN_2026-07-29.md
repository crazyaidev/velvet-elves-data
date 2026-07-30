# AWS Cost Attribution and Reduction Plan

Date: 2026-07-29
Author: Jan Froben
Account: `388482955098` (IAM user `crazyaidev`)
Method: read-only AWS CLI inventory (`aws ce`, `ec2`, `ecs`, `rds`, `elasticache`,
`elbv2`, `route53`, `cloudwatch`). **No resource was created, modified, stopped,
or deleted.** Every change below is a proposal awaiting approval.

Supersedes the AWS figures in `INITIAL_PRICE_ANALYSIS_2026-07-29.md` §3 and §8.

---

## 1. Headline correction

**Velvet Elves does not cost $596/month on AWS. It costs $278/month.**

The `/platform/costs` console calls Cost Explorer with `GroupBy=SERVICE` and **no
filter at all**, so it books every dollar in a shared AWS account to this
project. Account 388482955098 also hosts an unrelated project ("solstice"), and
that project is the larger of the two.

| | July 1-29 actual | Share |
| --- | --- | --- |
| **Velvet Elves** (us-east-2 + Route 53) | **$278.14** | 44% |
| **Solstice** (us-east-1, unrelated project) | $348.28 | 56% |
| Account total (what the console reports) | $626.42 | 100% |

The single clearest proof: **RDS is the largest line on the console at $129/month,
and there are zero RDS instances in us-east-2**, the only region Velvet Elves
deploys to. That database is `solstice-medusa-db`.

Velvet Elves run rate is **$297/month** (July 1-29 scaled to a 31-day month), of
which $55 is Textract, a genuine per-deal variable cost. **Fixed AWS is $242/month.**

The "AWS is doubling month over month" claim in the price analysis was also
measuring the wrong thing. Solstice's stack was built out in this period; Velvet
Elves stage came up 2026-06-26 and prod 2026-07-01, so its ramp is a one-time
step from zero to a running deployment, not runaway growth.

---

## 2. What belongs to whom (evidence)

| Evidence | Command | Result |
| --- | --- | --- |
| Velvet Elves ECS clusters | `ecs list-clusters --region us-east-2` | `velvet-elves-stage`, `velvet-elves-prod` |
| us-east-1 ECS cluster | `ecs list-services --cluster default --region us-east-1` | `solstice-api-4b2c`, `solstice-web-357e` |
| The $129/mo database | `rds describe-db-instances --region us-east-1` | `solstice-medusa-db`, db.t4g.medium, Multi-AZ, 200 GB |
| The $84.50/mo cache | `elasticache describe-serverless-caches --region us-east-1` | `solstice-redis` |
| RDS in the VE region | `rds describe-db-instances --region us-east-2` | **empty** |

Everything in us-east-1 (RDS $129.19, ElastiCache $84.50, ECS $66.96, VPC
$27.11, CloudWatch $17.41, ELB $15.26, EC2-Other $7.25) is Solstice. Velvet
Elves owns us-east-2 plus the `velvetelves.com` Route 53 zone.

Velvet Elves uses Supabase for Postgres, which is why it has no RDS at all. That
is the structural reason the attribution error was so large.

---

## 3. Complete Velvet Elves inventory and per-line cost

From `ce get-cost-and-usage --group-by USAGE_TYPE --filter REGION=us-east-2`:

| Line item | Resource | Jul 1-29 | Run rate |
| --- | --- | --- | --- |
| EC2 `t2.medium` x2 | `i-08526ef7dc3165151`, `i-0e1e8c02d19ac4489` | $74.95 | $80.12 |
| Textract | Forms $41.80 + Tables/Queries $8.47 + Sync $1.20 | $51.47 | $55.02 |
| Fargate vCPU-hours | 3 tasks (prod 2, stage 1) | $40.59 | $43.39 |
| NAT Gateway hours | `nat-02fde810e251d66f3` | $30.51 | $32.61 |
| ALB hours | `velvet-elves-stage-api-alb`, `velvet-elves-prod-api-alb` | $30.22 | $32.30 |
| Public IPv4 in-use | 7 addresses | $23.60 | $25.23 |
| Fargate GB-hours | 3 tasks | $8.91 | $9.52 |
| EBS gp2 80 GB | `vol-00a5d49be31f30e65` (legacy instance) | $7.26 | $7.76 |
| EBS gp3 64 GB | `vol-008f4900f61202a97` (dev instance) | $4.65 | $4.97 |
| EBS snapshots | 3 snapshots, oldest 2022-08 | $2.72 | $2.91 |
| NAT data processing | | $1.51 | $1.61 |
| Secrets Manager | 2 secrets | $0.74 | $0.79 |
| Route 53 | `velvetelves.com` zone, 46 records | $0.54 | $0.58 |
| Regional data transfer | | $0.33 | $0.35 |
| Misc (LCU, S3, ECR, KMS) | | $0.14 | $0.15 |
| **Total** | | **$278.14** | **$297.32** |

### 3.1 Compute topology

- **Fargate, not EC2, for the application.** Stage 1 task, prod 2 tasks, all
  512 CPU / 1024 MB. Prod at 2 tasks is deliberate (the stateless-Fernet OAuth
  fix exists precisely so 2 tasks are safe).
- **Prod and stage share one VPC** (`vpc-03f0ffdb29300e50f`,
  `velvet-elves-stage-vpc`), the same two private subnets, and the same NAT
  gateway. Both run `assignPublicIp: DISABLED`.
- **Both ALBs carry real traffic.** Prod 1,250 to 61,467 requests/day, stage
  1,156 to 32,564/day over the last 7 days. Neither is idle.
- **The 7 public IPv4 addresses** are 4 x ALB (2 AZs each), 1 x NAT, and 1 each
  on the two EC2 instances. None are unattached.

### 3.2 The two EC2 instances

These are the largest single line and they are not part of the Fargate stack.

| Instance | Name tag | Launched | Serves | CPU (14-day avg / max) |
| --- | --- | --- | --- | --- |
| `i-08526ef7dc3165151` | `velvetElves.com` | **2022-03-01** | `api.velvetelves.com`, `login.velvetelves.com` (3.140.33.46) | 1.07% / 46% |
| `i-0e1e8c02d19ac4489` | `velvet_elves_dev_server` | 2026-03-05 | `dev.velvetelves.com` (18.188.144.155) | 1.32% / 41% |

The 2022 instance is the **legacy pre-Fargate stack**. Current production is
`api.prod.velvetelves.com` on the prod ALB; `api.velvetelves.com` is the host
that caused the 2026-07-29 marketing incident (signups 404ing) precisely because
it is no longer the real API. Both instances idle at about 1% CPU with a daily
spike, so something scheduled still runs on them.

---

## 4. Two defects found while reading the task definitions

Both are drift between `.env` and the deployed ECS task definition, the exact
failure mode recorded after the 2026-07-21 staging incident.

**D-1. Prod extraction is checkbox-blind. (Correctness, not cost.)**

`velvet-elves-prod-backend:23` has **`TEXTRACT_OCR_ONLY_MODE=true`**. This is the
same setting that broke staging extraction on 2026-07-21 (checkbox-blind, null
title and inspection fields). Stage has since been corrected to `false`; **prod
was never corrected**. Any contract parsed in production right now is running
without form and selection-element detection.

This should be fixed regardless of the cost work, and it should be fixed before
the Textract feature-set change in §5, because the two interact.

**D-2. Textract is provisioned with every feature, not the intended two.**

Both task definitions set:

```
TEXTRACT_FEATURE_TYPES=FORMS,TABLES,QUERIES,SIGNATURES,LAYOUT
```

while `.env`, `.env.example`, `.env.stage`, `.env.prod`, and the `config.py`
default all say `FORMS,SIGNATURES`. AnalyzeDocument bills per feature, additively:

| Feature | List price / page |
| --- | --- |
| Forms | $0.050 |
| Tables | $0.015 |
| Queries | $0.015 |
| Layout | $0.010 |
| Signatures (combined) | $0.0035 |
| **Deployed set (all five)** | **~$0.0935** |
| **Intended set (Forms + Signatures)** | **~$0.0535** |

That is roughly **75% more per page than intended**. The billing data confirms
it: the usage type `USE2-AsyncFormsQueriesTablesPagesProcessed` is $8.47, and
that line should not exist at all under `FORMS,SIGNATURES`.

---

## 5. The reduction plan

Ordered by risk. Every step is reversible except where noted. Savings are
monthly run rate.

### Tier 1: no architecture change, immediately reversible ($90.49/mo)

**A-1. Stop both EC2 instances. Saves $80.12/mo.**

Stop, do not terminate, so the decision stays reversible for the price of the
EBS volumes ($12.73/mo, addressed in Tier 2).

```powershell
aws ec2 stop-instances --instance-ids i-08526ef7dc3165151 i-0e1e8c02d19ac4489 --region us-east-2
```

**Prerequisite, and this is a blocking check, not a formality.** Before stopping,
confirm what the daily CPU spike is. Log in to each instance and check for cron
jobs, and confirm nothing still calls `api.velvetelves.com`, `login.velvetelves.com`,
or `dev.velvetelves.com`. The three site repos were re-pinned per environment
after the 2026-07-29 incident, so the app side should be clean, but a scheduled
job, a webhook registered with a third party (SendGrid, Stripe, DocuSign, Google
Pub/Sub), or a bookmark could still depend on those hosts. Watch for 7 days after
stopping before proceeding to Tier 2.

**A-2. Delete the two 2022 EBS snapshots. Saves ~$1.90/mo.**

`snap-057f13f7613697683` (Velvet-9-Aug-22, 30 GB) and `snap-08863caaeb97bbff4`
(25 Aug 2022, 40 GB). Four years old and predating the current architecture.
Keep `snap-04cfacc0a09e0431b` (2025-03-20) until A-1 is confirmed.

**A-3. Correct `TEXTRACT_FEATURE_TYPES` to `FORMS,SIGNATURES` in both task
definitions. Saves $8.47/mo measured, likely $15 to $17/mo including Layout.**

Only the $8.47 Tables/Queries line is directly observable in the bill; the Layout
surcharge is folded into the Forms line, so I am claiming only the measured
figure. Register a new task definition revision for stage and prod with the
corrected value, matching what `.env` already specifies.

**A-4 (do first, no saving). Set `TEXTRACT_OCR_ONLY_MODE=false` in prod.**

Defect D-1. Prod extraction quality is currently degraded. Note that fixing this
will *increase* prod Textract spend, because prod is currently paying OCR-only
rates ($0.0015/page) for degraded output. A-3 partly offsets it. This is a
correctness fix that happens to have a cost consequence, and correctness wins.

### Tier 2: after the 7-day watch confirms the instances are dead ($20.03/mo)

**B-1. Snapshot, then delete, the two EBS volumes. Saves $12.73/mo.**

Take one final snapshot of each (`vol-00a5d49be31f30e65`,
`vol-008f4900f61202a97`), keep it for 90 days, then delete the volumes. A
snapshot of a 144 GB pair costs about $2/mo versus $12.73 for live volumes.

**B-2. Release the two Elastic IPs. Saves $7.30/mo.**

`3.140.33.46` and `18.188.144.155`. Note that a *stopped* instance keeps being
charged for its address at the idle rate, so A-1 alone does not capture this.
Releasing is irreversible (you cannot reclaim a specific IP), so remove the
`api.velvetelves.com`, `login.velvetelves.com`, and `dev.velvetelves.com` Route 53
records in the same change window.

### Tier 3: configuration change, low risk ($35.80/mo)

**C-1. Move the stage service to Fargate Spot. Saves $12.35/mo.**

Stage is a test environment; a Spot interruption means a task restart, which is
acceptable there. Set `capacityProviderStrategy` to `FARGATE_SPOT` on
`velvet-elves-stage-backend`. Do **not** do this for prod.

An alternative or complement is scheduling stage to `desiredCount=0` overnight
and at weekends, worth about $10/mo on its own. Spot is simpler and needs no
scheduler, and the two can be combined.

**C-2. Consolidate the two ALBs into one with host-based routing. Saves $23.45/mo
($16.15 ALB + $7.30 for two fewer public IPv4 addresses).**

One ALB, two listener rules on the existing HTTPS listener:
`api.prod.velvetelves.com` to the prod target group, `api.stage.velvetelves.com`
to the stage target group. Both certificates already exist in ACM and both
hostnames already resolve into this account.

Tradeoff to accept explicitly: stage and prod would share a load balancer. They
already share a VPC, subnets, and NAT gateway, so this does not introduce a new
class of coupling, but it does mean an ALB-level misconfiguration can affect
both. If Jake wants prod isolated, skip C-2 and accept the $23.45.

### Tier 4: architecture change, moderate effort ($23.29/mo)

**D-1. Remove the NAT gateway; run Fargate tasks in public subnets.**

Saves $32.61 NAT hours plus $1.61 data processing, costs $10.95 for three task
public IPv4 addresses. Net **$23.29/mo**.

Tasks would keep their security groups (inbound only from the ALB security
group), so they are not actually reachable from the internet; they simply get a
routable address for egress to Supabase, OpenAI, Anthropic, SendGrid, and Stripe.

I considered and rejected two alternatives:

- **VPC interface endpoints** instead of NAT: at $7.30/mo each, four endpoints
  (ECR api, ECR dkr, Secrets Manager, CloudWatch Logs) cost $29/mo and save
  nothing at this scale.
- **A NAT instance** on `t4g.nano` (~$3/mo): saves more on paper but introduces
  a single point of failure and a patching burden for a one-developer team.

This is the only item where I would understand a decision to leave the money on
the table. Public-subnet Fargate is a normal pattern, but it is a real change to
the network posture and should be reviewed rather than waved through.

### Tier 5: developer efficiency ($20/mo, and faster test cycles)

**E-1. Cache Textract responses by file content hash in dev and stage.**

Most Textract spend right now is not customer work. It is the same 12 test PDFs
in `velvet-elves-data/testing_pdfs/` and `testing_docs/` being re-parsed on every
wizard test run, at roughly $0.05 to $0.09 per page each time. A cache keyed on
SHA-256 of the file bytes, active only when `APP_ENV != production`, would
eliminate most repeat parses and remove a 30 to 90 second wait from every test
cycle.

Guard it behind an env flag and never enable it in prod, where every parse must
hit the real service.

---

## 6. Summary and revised economics

| Tier | Content | Saving |
| --- | --- | --- |
| 1 | Stop 2 EC2, delete 2 snapshots, fix Textract feature set | $90.49 |
| 2 | Delete 2 EBS volumes, release 2 EIPs | $20.03 |
| 3 | Stage on Spot, consolidate ALBs | $35.80 |
| 4 | Remove NAT, public-subnet Fargate | $23.29 |
| 5 | Textract cache for dev/stage | $20.00 |
| **Total** | | **$189.61/mo (64%)** |

AWS run rate falls from **$297/mo** to about **$108/mo**. Doing only Tiers 1 to 3,
which require no architecture review, gets it to about **$151/mo**.

### Effect on the pricing question

Fixed monthly cost, including the ~$99 of managed services still missing from the
console registry (Supabase, SendGrid, DocuSign, Google Cloud, domains):

| Scenario | Fixed / month |
| --- | --- |
| As reported by the console (wrong, includes Solstice) | $692 |
| **Corrected, today** | **$341** |
| After Tiers 1-3 | $203 |
| After all tiers | $180 |

Break-even volume, at the corrected $2.50 variable cost per deal:

| Fee | Console said | Corrected today | After T1-T3 | After all |
| --- | --- | --- | --- | --- |
| $20.00 | 42 deals/mo | **21** | 13 | 11 |
| $29.00 | 28 deals/mo | **14** | 9 | 8 |
| $50.00 | 16 deals/mo | **8** | 5 | 4 |

This materially changes the earlier answer on $20. I previously said $20 needs 42
deals/month and called that tight. **The real figure today is 21, and 13 after
the low-risk cleanup.** $20 per transaction is comfortable, not marginal, and the
argument against it is now purely about positioning against ListedKit's $14.99
rather than about cost recovery.

My recommendation of $29 stands on positioning grounds, but $20 is no longer the
financially aggressive choice it appeared to be.

---

## 7. Fixing the console so this does not recur

The attribution bug is in the AWS adapter, which calls Cost Explorer unfiltered.
Two changes make the console honest:

1. **Filter the Cost Explorer call to the Velvet Elves region.** Add
   `Filter={'Dimensions': {'Key': 'REGION', 'Values': ['us-east-2']}}` to the
   `get_cost_and_usage` call in `app/services/cost_sources/`. One line, and it
   removes 56% of the phantom cost immediately.
2. **Better: tag and filter by tag.** Apply a cost allocation tag such as
   `Project=velvet-elves` to the ECS clusters, ALBs, NAT gateway, and EC2
   instances, activate it in Billing, and filter on the tag instead of the
   region. Region filtering breaks the moment either project adds a region;
   tag filtering does not.

Until one of those ships, treat every AWS number on `/platform/costs` as roughly
double the truth. This is now the seventh known defect in that console; the other
six are listed in `INITIAL_PRICE_ANALYSIS_2026-07-29.md` §4.

---

## 8. Decisions needed before anything is executed

I have changed nothing. These need a human call:

1. **Are the two EC2 instances genuinely dead?** This is $80/mo, the single
   biggest item, and I cannot confirm it from outside. Someone has to look at
   what the daily CPU spike is and confirm no third party still calls
   `api.velvetelves.com`. (Jake's call on the business side, mine on the
   technical side.)
2. **Is prod allowed to share an ALB with stage?** (C-2, $23.45/mo.)
3. **Is public-subnet Fargate acceptable?** (Tier 4, $23.29/mo.)
4. **Prod is currently checkbox-blind** (D-1). This one is not a cost decision
   and in my view should be fixed this week regardless of everything above.
