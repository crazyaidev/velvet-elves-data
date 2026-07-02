# Velvet Elves - AWS ECS and CloudFront Stage/Production Deployment Plan

Date: 2026-06-25

Status: Planning document only. No source code changes are required by this document.

Target outcome:

- Move the FastAPI backend from EC2-hosted Docker to Amazon ECS on Fargate.
- Move the Vite/React frontend from EC2-hosted nginx Docker to S3 plus CloudFront.
- Adopt this branch-to-environment promotion model:
  - `develop`: local development branch. No automatic AWS deploy.
  - `main`: staging branch. Successful pushes deploy to the staging AWS stack.
  - `prod`: production branch. Successful pushes deploy to the production AWS stack.
- Keep Supabase as the database, auth, storage, and RLS authority.
- Use AWS CLI for AWS resource creation and deployment rather than the AWS Console.
- Preserve the current ability to deploy safely, verify health, and roll back.

---

## 1. Project-Specific Facts This Plan Uses

These facts come from the current project docs and app manifests.

- Backend: `velvet-elves-backend`
  - FastAPI app in Docker.
  - Dockerfile exposes port `8000`.
  - Runtime command is `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
  - Liveness endpoints exist at `/api/health`, `/api/v1/health`, and `/health`.
  - Readiness endpoint exists at `/api/v1/health/ready` and checks Supabase connectivity.
  - The backend depends on Supabase, OpenAI/Anthropic, AWS Textract/S3, SendGrid, DocuSign, Google/Microsoft email/calendar OAuth, Gmail Pub/Sub, Microsoft Graph webhooks, and Stripe.
  - The current production workflow builds a Docker image, pushes it to GHCR, runs Supabase migrations, configures the Textract bucket, SSHes into EC2, writes `.env`, and restarts Docker Compose.
  - The current workflow is triggered by `main`; this plan changes the intended target state so `main` becomes staging and `prod` becomes production.

- Frontend: `velvet-elves-frontend`
  - Vite, React 18, TypeScript.
  - Production build command: `npm run build`.
  - Built output directory: `dist`.
  - `VITE_API_BASE_URL` is a build-time value and must be set before `npm run build`.
  - Current frontend Docker/nginx config has SPA fallback to `index.html`.
  - Current nginx config explicitly serves `.mjs` files as JavaScript because the PDF worker can fail if `.mjs` is served with the wrong MIME type. The S3/CloudFront deployment must verify `.mjs` metadata.

- Current public dev references in docs:
  - Current shared dev frontend/backend origin: `https://dev.velvetelves.com`.
  - Keep `dev.velvetelves.com` unchanged during this migration.
  - `velvet-elves-frontend` and `velvet-elves-backend` are the core product app repositories.
  - The marketing website and help center are separate web surfaces. Their domains must be reserved and protected during this migration, but their application deployment is outside the backend/frontend ECS and CloudFront cutover unless explicitly added later.
  - Final domain model:
    - `STAGE_MARKETING_DOMAIN`: `stage.velvetelves.com`.
    - `STAGE_APP_DOMAIN`: `app.stage.velvetelves.com`.
    - `STAGE_API_DOMAIN`: `api.stage.velvetelves.com`.
    - `STAGE_HELP_DOMAIN`: `help.stage.velvetelves.com`.
    - `PROD_MARKETING_DOMAIN`: `velvetelves.com`.
    - `PROD_APP_DOMAIN`: `app.velvetelves.com`.
    - `PROD_API_DOMAIN`: `api.prod.velvetelves.com`.
    - `PROD_HELP_DOMAIN`: `help.velvetelves.com`.
  - DNS is currently managed in GoDaddy. Use GoDaddy for production and staging DNS records for now. Route 53 DNS hosting and domain registrar transfer are future follow-up items after the AWS migration is stable.

---

## 1.1 Branch and Environment Strategy

This plan uses three branches with explicit promotion semantics.

| Branch | Purpose | AWS deploy? | GitHub environment | Data/provider targets |
| --- | --- | --- | --- | --- |
| `develop` | Local development and integration work | No automatic AWS deploy | none | local `.env`, local/dev Supabase as needed |
| `main` | Staging | Yes, to staging ECS/CloudFront | `staging` | staging Supabase and staging/test provider credentials |
| `prod` | Production | Yes, to production ECS/CloudFront | `production` | production Supabase and production provider credentials |

Promotion flow:

1. Developers work locally from `develop` or short-lived feature branches based on `develop`.
2. Merge `develop` into `main` only when the build is ready for staging.
3. Push to `main` deploys the staging backend and frontend.
4. Run the staging validation checklist against `STAGE_APP_DOMAIN` and `STAGE_API_DOMAIN`.
5. Promote the exact staged commit from `main` to `prod`.
6. Push to `prod` deploys the production backend and frontend.

Production should be promoted from a known-good `main` commit. Do not merge unvalidated feature work directly into `prod`.

---

## 1.2 Stage-by-Stage Execution Plan

Proceed in stages. Each stage has a clear output, verification gate, stop rule, and next-stage unlock condition. Do not advance to the next stage until the current stage's verification gate is complete.

### Stage 0 - Baseline, Branch, and Access Readiness

Goal: prepare the release structure without changing live traffic.

Actions:

1. Confirm the current EC2 deployment is healthy and represents the current production baseline.
2. Confirm `main` is the branch currently matching production.
3. Create `prod` from `main` if it does not already exist.
4. Keep `develop` as the local/integration branch.
5. Inventory current GitHub Actions secrets, EC2 `.env` values, DNS records, provider callbacks, Supabase project settings, and Textract bucket settings.
6. Confirm final values for marketing, app, API, and help center domains:
   - `STAGE_MARKETING_DOMAIN=stage.velvetelves.com`
   - `STAGE_APP_DOMAIN=app.stage.velvetelves.com`
   - `STAGE_API_DOMAIN=api.stage.velvetelves.com`
   - `STAGE_HELP_DOMAIN=help.stage.velvetelves.com`
   - `PROD_MARKETING_DOMAIN=velvetelves.com`
   - `PROD_APP_DOMAIN=app.velvetelves.com`
   - `PROD_API_DOMAIN=api.prod.velvetelves.com`
   - `PROD_HELP_DOMAIN=help.velvetelves.com`
7. Confirm AWS CLI access, Docker access, Supabase CLI access, and GoDaddy DNS change access.
8. Do not change CI/CD triggers yet unless there is already a safe staging target.

Verification gate:

- `prod` exists and points to the same commit as `main` at creation time.
- Current EC2 frontend and backend health checks pass.
- Current rollback path is understood and documented.
- All required secrets are inventoried, but no secrets are committed.
- GoDaddy DNS access and certificate validation ownership are confirmed.
- Existing email-related DNS records are inventoried before any DNS change.

Stop rule:

- Stop if `main` does not match current production or if current production is unstable.
- Stop if provider callback ownership is unclear.
- Stop if company email DNS records are not fully inventoried.

Unlocks:

- Stage 1 can begin when the current production baseline is known and the `prod` branch exists.

### Stage 1 - Staging AWS Foundation

Goal: create the staging AWS foundation without touching production traffic.

Actions:

1. Set `$ENV_NAME = "stage"`.
2. Create or select VPC, public subnets, private subnets, routing, NAT, and optional VPC endpoints.
3. Create staging ALB and ECS security groups.
4. Request staging ACM certificates for `STAGE_API_DOMAIN` in `$REGION` and `STAGE_APP_DOMAIN` in `us-east-1`.
   - If the staging marketing or help center surfaces are hosted on AWS, also request/validate certificates for `STAGE_MARKETING_DOMAIN` and `STAGE_HELP_DOMAIN` in the region required by their hosting service.
5. Create or reuse the ECR repository.
6. Create the staging CloudWatch log group.
7. Create the staging Secrets Manager secret at `/velvet-elves/stage/backend`.
8. Create staging IAM roles and policies for ECS execution and backend task runtime.
9. Create or configure the staging Textract S3 bucket.

Verification gate:

- Staging ACM certificates are `ISSUED`.
- Staging security groups allow public `80/443` only to ALB and `8000` only from ALB to ECS tasks.
- Staging secret exists and contains only staging values.
- Staging log group exists and retention is set.
- Staging Textract bucket is private, encrypted, and has cleanup lifecycle.
- No production AWS resources were changed.

Stop rule:

- Stop if any staging secret points to a production Supabase project or production provider credential.
- Stop if certificates are not issued.

Unlocks:

- Stage 2 can begin when the staging foundation is provisioned and isolated.

### Stage 2 - Staging Backend on ECS

Goal: deploy the backend from `main` to the staging ECS stack.

Actions:

1. Merge or push the intended commit to `main`.
2. Build the backend Docker image.
3. Push to ECR with `main-<sha>` and optionally `stage-latest`.
4. Apply migrations to the staging Supabase project only.
5. Register the staging backend task definition.
6. Create or update the `velvet-elves-stage-backend` ECS service.
7. Attach the service to the staging ALB target group.
8. Create `STAGE_API_DOMAIN` DNS in GoDaddy as a CNAME to the staging ALB DNS name.

Verification gate:

- ECS desired count equals running count.
- ALB target group shows healthy targets.
- CloudWatch receives staging backend logs.
- `GET https://STAGE_API_DOMAIN/api/health` returns `200`.
- `GET https://STAGE_API_DOMAIN/api/v1/health/ready` returns `200`.
- Staging backend can reach staging Supabase.
- Staging backend can call Textract/S3 using task-role credentials.

Stop rule:

- Stop if migrations accidentally target production.
- Stop if readiness fails or logs show missing required environment variables.

Unlocks:

- Stage 3 can begin when the staging API is healthy behind the staging ALB.

### Stage 3 - Staging Frontend on S3 and CloudFront

Goal: deploy the frontend from `main` to the staging S3/CloudFront stack.

Actions:

1. Build with `VITE_API_BASE_URL=https://STAGE_API_DOMAIN` and `VITE_APP_ENV=staging`.
2. Create the staging frontend S3 bucket if it does not exist.
3. Upload hashed assets with long cache headers.
4. Upload `.mjs` assets with `text/javascript`.
5. Upload `index.html` with no-cache headers.
6. Create staging CloudFront OAC, cache policy, SPA rewrite function, distribution, and bucket policy.
7. Create `STAGE_APP_DOMAIN` DNS in GoDaddy as a CNAME to staging CloudFront.
8. Invalidate `/` and `/index.html`.

Verification gate:

- `https://STAGE_APP_DOMAIN/` loads.
- Hard refresh works on `/login`, `/dashboard`, `/transactions/active`, and `/settings`.
- Browser network calls go to `https://STAGE_API_DOMAIN`.
- No CORS or mixed-content errors appear.
- PDF worker `.mjs` loads with JavaScript MIME type.
- A deliberately missing asset returns real `403` or `404`, not `200 text/html`.

Stop rule:

- Stop if the staging frontend calls the production API.
- Stop if `.mjs` files are served as HTML or `application/octet-stream`.

Unlocks:

- Stage 4 can begin when the staging frontend and backend work together end-to-end.

### Stage 4 - Staging Provider and Workflow Validation

Goal: prove application workflows in staging before production promotion.

Actions:

1. Configure staging Supabase Auth URLs.
2. Configure staging or sandbox OAuth callback URLs for Google, Microsoft, and DocuSign.
3. Configure the staging or test Stripe webhook endpoint.
4. Configure staging email/calendar webhook endpoints where safe.
5. Run the full environment validation checklist against staging.
6. Record the validated `main` commit SHA.

Verification gate:

- Login, logout, password reset, and invite acceptance work on staging.
- Authenticated API calls succeed.
- Document upload and Textract-backed parsing work.
- AI parsing or suggestions can reach the configured staging AI provider.
- Stripe webhook validation works in test mode.
- DocuSign sandbox callback/webhook works if sandbox credentials are available.
- Gmail/Outlook OAuth callback works with staging redirect URIs if test credentials are available.

Stop rule:

- Stop if any staging callback or webhook points to production domains by mistake.
- Stop if staging cannot complete core auth, transaction, upload, and document parsing flows.

Unlocks:

- Stage 5 can begin when the exact `main` commit is approved for production promotion.

### Stage 5 - CI/CD Branch Split

Goal: make branch behavior match the target promotion model.

Actions:

1. Update backend workflow triggers for PRs and pushes to `main` and `prod`.
2. Update frontend workflow triggers the same way.
3. Configure `github.ref_name == 'main'` to use `ENV_NAME=stage`, GitHub environment `staging`, and staging secrets/domains.
4. Configure `github.ref_name == 'prod'` to use `ENV_NAME=prod`, GitHub environment `production`, and production secrets/domains.
5. Add or confirm branch protections:
   - `main`: PR and CI required.
   - `prod`: PR, CI, approval, and restricted direct pushes.
6. Ensure `develop` has no automatic AWS deployment.

Verification gate:

- A test push or merge to `main` deploys only staging.
- No production deployment runs from `main`.
- A dry run or controlled test confirms `prod` is the only production deploy branch.
- GitHub environment secrets are separated between `staging` and `production`.

Stop rule:

- Stop if `main` can still deploy production.
- Stop if staging and production workflows share the same secret values accidentally.

Unlocks:

- Stage 6 can begin when CI/CD branch behavior is correct and staging deploys automatically from `main`.

### Stage 6 - Production AWS Foundation

Goal: create the production ECS/CloudFront foundation without moving live traffic yet.

Actions:

1. Set `$ENV_NAME = "prod"`.
2. Create production security groups, certificates, log group, Secrets Manager secret, IAM roles, and Textract bucket configuration.
3. Confirm production secrets are production values only.
4. Create production ALB, target group, ECS cluster, and frontend S3/CloudFront resources.
5. Keep existing EC2 production DNS serving users until cutover.
6. Do not change `dev.velvetelves.com`, `PROD_MARKETING_DOMAIN`, or `PROD_HELP_DOMAIN` while provisioning the production app/API stack.

Verification gate:

- Production ACM certificates are `ISSUED`.
- Production secret exists and contains production values only.
- Production ECS and CloudFront resources exist.
- Production ALB and CloudFront are reachable on AWS-generated domains before public DNS cutover where possible.
- Existing EC2 production remains healthy.
- `dev.velvetelves.com`, the marketing site, the help center, and company email DNS records remain unchanged.

Stop rule:

- Stop if production secrets are incomplete or provider credentials are not confirmed.
- Stop if creating production resources disrupts EC2 production.

Unlocks:

- Stage 7 can begin when production infrastructure exists and EC2 remains the live serving path.

### Stage 7 - Production Deployment From `prod`

Goal: deploy the validated staged commit to the production ECS/CloudFront stack.

Actions:

1. Promote the exact validated `main` commit to `prod`.
2. Let `prod` deploy the production backend image to ECS.
3. Apply production Supabase migrations only after confirming they are backward-compatible or inside the maintenance window.
4. Let `prod` deploy the production frontend build to S3/CloudFront.
5. Keep DNS pointing at EC2 until ECS/CloudFront production smoke tests pass.

Verification gate:

- Production ECS service is stable.
- Production ALB target group has healthy targets.
- Production backend health and readiness checks pass.
- Production frontend build points to `https://PROD_API_DOMAIN`.
- CloudFront distribution is deployed.

Stop rule:

- Stop if production backend readiness fails.
- Stop if frontend was built with staging API URL.
- Stop if production migrations fail.

Unlocks:

- Stage 8 can begin when production ECS/CloudFront are healthy and ready for DNS/provider cutover.

### Stage 8 - Production DNS and Provider Cutover

Goal: move real production traffic from EC2 to ECS/CloudFront.

Actions:

1. Lower DNS TTLs at least 24 hours before cutover where possible.
2. Announce maintenance window if needed.
3. Pause old EC2 deploy workflows.
4. Update production provider callback URLs for Supabase Auth, Google/Microsoft OAuth, Google Pub/Sub, Microsoft Graph, DocuSign, and Stripe.
5. Update GoDaddy DNS:
   - `PROD_API_DOMAIN` as a CNAME to the production ALB DNS name.
   - `PROD_APP_DOMAIN` as a CNAME to the production CloudFront domain name.
   - Do not change `PROD_MARKETING_DOMAIN`, `PROD_HELP_DOMAIN`, company email records, or `dev.velvetelves.com` in this cutover unless a separate marketing/help change is explicitly scheduled.
6. Force a new ECS deployment if only secret values changed; otherwise update ECS to the latest task definition revision.
7. Run smoke tests from a clean browser session.

Verification gate:

- `PROD_APP_DOMAIN` loads the SPA.
- `PROD_API_DOMAIN` health and readiness return `200`.
- `PROD_MARKETING_DOMAIN`, `PROD_HELP_DOMAIN`, and `dev.velvetelves.com` still resolve to their intended existing targets.
- Company email continues to receive and send normally.
- Login and authenticated API call work.
- No CORS or mixed-content errors appear.
- Stripe webhook mode is confirmed as intended.
- DocuSign Connect delivery succeeds or is queued/retryable.
- CloudWatch logs show normal traffic and no secret leakage.

Stop rule:

- Roll back DNS if core login, API readiness, or frontend boot fails and cannot be fixed quickly.
- Keep EC2 warm until the confidence window is complete.

Unlocks:

- Stage 9 begins immediately after DNS/provider cutover.

### Stage 9 - Post-Cutover Monitoring and Stabilization

Goal: observe production, handle regressions, and delay decommissioning until confidence is earned.

Actions:

1. Monitor ALB, ECS, CloudFront, backend logs, Stripe, DocuSign, Gmail/Outlook webhooks, and Supabase.
2. Run the production validation checklist at cutover, after 30 minutes, after 2 hours, and the next business day.
3. Keep EC2 warm for at least 7 days.
4. Disable old EC2 deploys after ECS is confirmed as the production path.
5. Document issues, mitigations, and follow-up work.

Verification gate:

- Error rates remain within expected thresholds.
- ECS desired count equals running count.
- No repeated task crashes occur.
- User flows remain healthy.
- Provider webhooks continue delivering to production ECS endpoints.

Stop rule:

- If production instability persists, roll back through the rollback plan and do not decommission EC2.

Unlocks:

- Stage 10 can begin after the agreed confidence window.

### Stage 10 - EC2 Decommission and Cleanup

Goal: remove the old EC2 serving path only after the new architecture is proven.

Actions:

1. Confirm production has served successfully from ECS/CloudFront for the agreed confidence window.
2. Export or archive EC2 logs if required.
3. Remove old provider callback URLs that are no longer needed.
4. Stop EC2 instances before terminating them.
5. Delete old EC2-only security groups, load balancers, volumes, and DNS records only after final approval.
6. Rotate any secrets that were broadly copied during migration.
7. Update documentation to show `develop -> main(stage) -> prod(production)` as the active operating model.

Verification gate:

- No production app/API DNS records point to EC2.
- `dev.velvetelves.com` remains available until its separate retirement plan exists.
- No provider webhooks point to EC2.
- GitHub Actions no longer SSH to EC2 for deploys.
- Cost and resource inventory no longer show unused EC2 deployment resources.

Stop rule:

- Do not terminate EC2 if any rollback dependency still points to it.

---

## 2. Recommended Target Architecture

```text
Browser
  |
  | HTTPS
  v
CloudFront distribution
  |
  | Origin Access Control
  v
Private S3 bucket holding Vite dist/

Browser
  |
  | HTTPS API calls to https://API_DOMAIN
  v
Public Application Load Balancer
  |
  | HTTP port 8000, target type ip
  v
ECS Fargate service in private subnets
  |
  | outbound HTTPS
  v
Supabase, OpenAI/Anthropic, Stripe, DocuSign, Google/Microsoft, SendGrid

ECS Fargate task role
  |
  | AWS SDK calls
  v
Textract + private Textract input S3 bucket
```

Separate public web surfaces:

- Marketing website:
  - Staging: `stage.velvetelves.com`
  - Production: `velvetelves.com`
- Product frontend:
  - Staging: `app.stage.velvetelves.com`
  - Production: `app.velvetelves.com`
- Backend API:
  - Staging: `api.stage.velvetelves.com`
  - Production: `api.prod.velvetelves.com`
- Help center:
  - Staging: `help.stage.velvetelves.com`
  - Production: `help.velvetelves.com`
- Existing dev server:
  - `dev.velvetelves.com` remains unchanged until a separate dev-environment retirement or replacement plan exists.

This ECS/CloudFront migration covers the product frontend and backend API. Marketing and help center deployment details should be handled in separate plans unless they are deliberately folded into this infrastructure work.

Recommended resource names:

| Resource | Staging from `main` | Production from `prod` |
| --- | --- | --- |
| AWS region | `us-east-2` unless the current AWS account standard says otherwise | same region unless there is a deliberate DR strategy |
| ECS cluster | `velvet-elves-stage` | `velvet-elves-prod` |
| ECS service | `velvet-elves-stage-backend` | `velvet-elves-prod-backend` |
| ECR repository | `velvet-elves/backend` | `velvet-elves/backend` |
| Backend image tag | `main-<sha>` and `stage-latest` | `prod-<sha>` and `prod-latest` |
| ALB | `velvet-elves-stage-api-alb` | `velvet-elves-prod-api-alb` |
| ALB target group | `velvet-elves-stage-api-tg` | `velvet-elves-prod-api-tg` |
| Backend log group | `/ecs/velvet-elves/stage/backend` | `/ecs/velvet-elves/prod/backend` |
| Backend secret | `/velvet-elves/stage/backend` | `/velvet-elves/prod/backend` |
| Frontend S3 bucket | `velvet-elves-stage-frontend-<account-id>` | `velvet-elves-prod-frontend-<account-id>` |
| Frontend CloudFront OAC | `velvet-elves-stage-frontend-oac` | `velvet-elves-prod-frontend-oac` |
| Textract S3 bucket | staging bucket from staging `TEXTRACT_S3_BUCKET` | production bucket from production `TEXTRACT_S3_BUCKET` |

Staging and production must be separate AWS/runtime environments:

- Staging uses staging Supabase, staging/test provider credentials, staging callback URLs, and staging CloudFront/ALB domains.
- Production uses production Supabase, production provider credentials, production callback URLs, and production CloudFront/ALB domains.

If only one Supabase project exists today, create a staging Supabase project or use a clone before treating `main` as staging. Do not use production ECS as the first test bed for destructive migration checks.

---

## 3. Environment Domain and Certificate Decisions

Make these decisions before provisioning.

| Decision | Recommendation |
| --- | --- |
| Existing dev domain | Keep `dev.velvetelves.com` unchanged |
| Staging marketing domain | `STAGE_MARKETING_DOMAIN=stage.velvetelves.com` |
| Staging frontend domain | `STAGE_APP_DOMAIN=app.stage.velvetelves.com` |
| Staging API domain | `STAGE_API_DOMAIN=api.stage.velvetelves.com` |
| Staging help center domain | `STAGE_HELP_DOMAIN=help.stage.velvetelves.com` |
| Production marketing domain | `PROD_MARKETING_DOMAIN=velvetelves.com` |
| Production frontend domain | `PROD_APP_DOMAIN=app.velvetelves.com` |
| Production API domain | `PROD_API_DOMAIN=api.prod.velvetelves.com` |
| Production help center domain | `PROD_HELP_DOMAIN=help.velvetelves.com` |
| Backend certificate | ACM certificate in the same region as each environment's ALB, likely `us-east-2` |
| CloudFront certificate | ACM certificate for each CloudFront-hosted frontend, marketing, or help center domain in `us-east-1` |
| DNS | Use GoDaddy DNS for now. Use CNAME records for app/API/help subdomains. Move DNS hosting to Route 53 later in a separate controlled migration. |
| API TLS termination | ALB terminates HTTPS on port `443`, forwards HTTP to ECS target port `8000` |
| Frontend TLS termination | CloudFront terminates HTTPS |

Important CloudFront certificate rule: CloudFront viewer certificates from ACM must be requested or imported in `us-east-1`.

Important GoDaddy DNS notes:

- Preserve all company email DNS records before any change: `MX`, SPF `TXT`, DKIM records, DMARC, provider verification records, `autodiscover`, and any mail-related `CNAME` or `SRV` records.
- Subdomains such as `app.velvetelves.com`, `api.prod.velvetelves.com`, `help.velvetelves.com`, `app.stage.velvetelves.com`, and `api.stage.velvetelves.com` can be pointed with CNAME records.
- The apex `velvetelves.com` cannot use a normal DNS CNAME. If the production marketing site is hosted on CloudFront while DNS remains in GoDaddy, confirm GoDaddy's supported apex record/forwarding option or move DNS hosting to Route 53 before apex CloudFront cutover.
- Do not transfer the domain registrar from GoDaddy to Route 53 during the ECS/CloudFront app cutover. If Route 53 is desired later, first migrate DNS hosting safely, verify website/app/API/help/email behavior, then transfer registration.

In the command sections below, set `APP_DOMAIN` and `API_DOMAIN` to the domain pair for the environment being provisioned:

- For staging: `APP_DOMAIN=$STAGE_APP_DOMAIN`, `API_DOMAIN=$STAGE_API_DOMAIN`, `ENV_NAME=stage`.
- For production: `APP_DOMAIN=$PROD_APP_DOMAIN`, `API_DOMAIN=$PROD_API_DOMAIN`, `ENV_NAME=prod`.

### 3.1 Future Route 53 DNS and Registrar Migration

Route 53 is a good later target, but it should not be bundled into the ECS/CloudFront app/API cutover.

Recommended future sequence:

1. Keep GoDaddy as registrar and DNS provider during the initial AWS migration.
2. After ECS/CloudFront production is stable, create a Route 53 public hosted zone for `velvetelves.com`.
3. Copy every GoDaddy DNS record into Route 53, including all website, app, API, help center, email, verification, and provider records.
4. Lower relevant GoDaddy TTLs before changing nameservers.
5. Change GoDaddy nameservers to the four Route 53 hosted-zone nameservers.
6. Monitor marketing, app, API, help center, company email, and provider callbacks.
7. Only after Route 53 DNS hosting is stable, optionally transfer domain registration from GoDaddy to Route 53.

Do not transfer DNS hosting and registrar ownership at the same time. If anything goes wrong during DNS migration, revert the nameservers in GoDaddy to the previous GoDaddy nameservers.

---

## 4. Local CLI Setup

All AWS commands should be run from an authenticated shell. Examples are PowerShell-friendly.

```powershell
$REGION = "us-east-2"
$CF_CERT_REGION = "us-east-1"
$ENV_NAME = "stage" # stage for main, prod for prod
$STAGE_MARKETING_DOMAIN = "stage.velvetelves.com"
$STAGE_APP_DOMAIN = "app.stage.velvetelves.com"
$STAGE_API_DOMAIN = "api.stage.velvetelves.com"
$STAGE_HELP_DOMAIN = "help.stage.velvetelves.com"
$PROD_MARKETING_DOMAIN = "velvetelves.com"
$PROD_APP_DOMAIN = "app.velvetelves.com"
$PROD_API_DOMAIN = "api.prod.velvetelves.com"
$PROD_HELP_DOMAIN = "help.velvetelves.com"

if ($ENV_NAME -eq "stage") {
  $MARKETING_DOMAIN = $STAGE_MARKETING_DOMAIN
  $APP_DOMAIN = $STAGE_APP_DOMAIN
  $API_DOMAIN = $STAGE_API_DOMAIN
  $HELP_DOMAIN = $STAGE_HELP_DOMAIN
} elseif ($ENV_NAME -eq "prod") {
  $MARKETING_DOMAIN = $PROD_MARKETING_DOMAIN
  $APP_DOMAIN = $PROD_APP_DOMAIN
  $API_DOMAIN = $PROD_API_DOMAIN
  $HELP_DOMAIN = $PROD_HELP_DOMAIN
} else {
  throw "ENV_NAME must be stage or prod"
}

$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
$NAME_PREFIX = "velvet-elves-$ENV_NAME"
$BACKEND_SECRET_NAME = "/velvet-elves/$ENV_NAME/backend"
$BACKEND_LOG_GROUP = "/ecs/velvet-elves/$ENV_NAME/backend"
$FRONTEND_BUCKET = "velvet-elves-$ENV_NAME-frontend-$ACCOUNT_ID"
$ECR_REPOSITORY = "velvet-elves/backend"

aws sts get-caller-identity
aws configure get region
```

If `aws configure get region` does not return the intended region:

```powershell
aws configure set region $REGION
```

Create a local working folder for generated JSON files during implementation. Do not commit real secrets.

```powershell
New-Item -ItemType Directory -Force .\aws-deploy-work
```

---

## 5. Phase 0 - Pre-Migration Discovery

### 5.1 Inventory the Current EC2 Deployment

Record these values from the current EC2 deployment before creating AWS replacements:

- Existing frontend public URL.
- Existing backend public URL.
- Existing DNS records and TTLs.
- Current GoDaddy account owner/admins, 2FA status, domain lock status, auto-renewal status, and recovery email.
- Current company email DNS records:
  - `MX`.
  - SPF `TXT`.
  - DKIM `TXT` or `CNAME`.
  - DMARC.
  - Microsoft/Google/provider verification records.
  - `autodiscover`, `autoconfig`, and any mail-related `CNAME` or `SRV` records.
- Existing EC2 security groups.
- Existing `.env` values, but store them in a password manager or AWS Secrets Manager, not in this markdown file.
- Current `TEXTRACT_S3_BUCKET`, `TEXTRACT_S3_PREFIX`, and AWS region.
- Current GitHub Actions secrets.
- Current provider callback URLs:
  - Supabase Auth Site URL and redirect URLs.
  - Google Gmail OAuth callback.
  - Microsoft Outlook OAuth callback.
  - Google Calendar OAuth callback.
  - Microsoft Calendar OAuth callback.
  - DocuSign OAuth callback.
  - DocuSign Connect webhook URL.
  - Stripe webhook URL.
  - Gmail Pub/Sub push subscription endpoint.
  - Microsoft Graph subscription notification endpoint.

### 5.2 Freeze Risky Changes

Before cutover week:

- Avoid schema migrations that are not backward-compatible with the current EC2 backend.
- Avoid changing auth callback paths.
- Avoid changing frontend routing.
- Avoid rotating provider credentials unless the rotation is part of this migration.

### 5.3 Confirm Supabase State

Because Supabase remains the system of record:

- Confirm production Supabase backups and point-in-time recovery status.
- Confirm the production `SUPABASE_DB_URL` uses the Supabase pooler.
- Confirm RLS policies are already applied and tested.
- Confirm Supabase Auth allowed redirect URLs include the future `APP_DOMAIN`.

---

## 6. Phase 1 - AWS Foundation

### 6.1 VPC and Subnets

Recommended production network:

- One VPC.
- At least two Availability Zones.
- Public subnets for the ALB.
- Private subnets for ECS tasks.
- NAT Gateway or equivalent outbound egress because the backend calls external SaaS APIs.
- Optional VPC endpoints for AWS services:
  - ECR API and ECR Docker.
  - CloudWatch Logs.
  - Secrets Manager.
  - S3 Gateway endpoint.
  - Textract if available in the chosen region.

If a suitable VPC already exists, capture IDs:

```powershell
aws ec2 describe-vpcs --region $REGION --query "Vpcs[].{VpcId:VpcId,CidrBlock:CidrBlock,IsDefault:IsDefault,Tags:Tags}" --output table
aws ec2 describe-subnets --region $REGION --filters Name=vpc-id,Values=<vpc-id> --query "Subnets[].{SubnetId:SubnetId,Az:AvailabilityZone,CidrBlock:CidrBlock,MapPublicIp:MapPublicIpOnLaunch}" --output table
```

Set variables after choosing subnets:

```powershell
$VPC_ID = "vpc-xxxxxxxx"
$PUBLIC_SUBNET_1 = "subnet-public-a"
$PUBLIC_SUBNET_2 = "subnet-public-b"
$PRIVATE_SUBNET_1 = "subnet-private-a"
$PRIVATE_SUBNET_2 = "subnet-private-b"
```

### 6.2 Security Groups

Create an ALB security group:

```powershell
$ALB_SG = aws ec2 create-security-group `
  --group-name "$NAME_PREFIX-api-alb-sg" `
  --description "Velvet Elves $ENV_NAME API ALB" `
  --vpc-id $VPC_ID `
  --region $REGION `
  --query GroupId --output text

aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $REGION
aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $REGION
```

Create an ECS task security group:

```powershell
$ECS_SG = aws ec2 create-security-group `
  --group-name "$NAME_PREFIX-backend-task-sg" `
  --description "Velvet Elves $ENV_NAME backend ECS tasks" `
  --vpc-id $VPC_ID `
  --region $REGION `
  --query GroupId --output text

aws ec2 authorize-security-group-ingress `
  --group-id $ECS_SG `
  --protocol tcp `
  --port 8000 `
  --source-group $ALB_SG `
  --region $REGION
```

ECS tasks should not have public inbound access. Outbound should allow HTTPS to Supabase, provider APIs, and AWS services. Start with default outbound and tighten later once VPC endpoints and egress requirements are known.

### 6.3 ACM Certificates

Request the API certificate in the backend region:

```powershell
$API_CERT_ARN = aws acm request-certificate `
  --region $REGION `
  --domain-name $API_DOMAIN `
  --validation-method DNS `
  --query CertificateArn --output text
```

Request the CloudFront certificate in `us-east-1`:

```powershell
$APP_CERT_ARN = aws acm request-certificate `
  --region $CF_CERT_REGION `
  --domain-name $APP_DOMAIN `
  --validation-method DNS `
  --query CertificateArn --output text
```

Use `describe-certificate` to get DNS validation records:

```powershell
aws acm describe-certificate --region $REGION --certificate-arn $API_CERT_ARN
aws acm describe-certificate --region $CF_CERT_REGION --certificate-arn $APP_CERT_ARN
```

If DNS is hosted in Route 53, create the validation CNAMEs via `aws route53 change-resource-record-sets`. If DNS is not hosted in Route 53, add the CNAMEs at the DNS provider.

Current DNS provider decision:

- `velvetelves.com` is currently managed in GoDaddy.
- Add ACM validation CNAMEs in GoDaddy for this migration.
- Do not change the domain's authoritative nameservers during the ECS/CloudFront cutover.
- Preserve all email records while adding validation, app, API, and later help/marketing records.

### 6.4 ECR Repository

```powershell
aws ecr create-repository `
  --repository-name velvet-elves/backend `
  --image-scanning-configuration scanOnPush=true `
  --encryption-configuration encryptionType=AES256 `
  --region $REGION
```

Recommended lifecycle policy:

```json
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep the most recent 30 tagged images",
      "selection": {
        "tagStatus": "tagged",
        "countType": "imageCountMoreThan",
        "countNumber": 30
      },
      "action": {
        "type": "expire"
      }
    },
    {
      "rulePriority": 2,
      "description": "Expire untagged images after 7 days",
      "selection": {
        "tagStatus": "untagged",
        "countType": "sinceImagePushed",
        "countUnit": "days",
        "countNumber": 7
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
```

Save as `aws-deploy-work\ecr-lifecycle.json`, then:

```powershell
aws ecr put-lifecycle-policy `
  --repository-name velvet-elves/backend `
  --lifecycle-policy-text file://aws-deploy-work/ecr-lifecycle.json `
  --region $REGION
```

### 6.5 CloudWatch Logs

```powershell
aws logs create-log-group --log-group-name $BACKEND_LOG_GROUP --region $REGION
aws logs put-retention-policy --log-group-name $BACKEND_LOG_GROUP --retention-in-days 30 --region $REGION
```

Use a longer retention period if legal/compliance requires API logs to be retained. Avoid logging PII and secrets.

---

## 7. Phase 2 - Backend on ECS Fargate

### 7.1 Backend Runtime Environment

The current backend expects environment variables. In ECS, use:

- Plain task-definition `environment` entries for non-secret values.
- Task-definition `secrets` entries backed by AWS Secrets Manager for sensitive values.

Recommended non-secret environment values:

```text
APP_ENV=<staging-or-production>
APP_DEBUG=false
FRONTEND_URL=https://APP_DOMAIN
CORS_ORIGINS=https://APP_DOMAIN
AI_PROVIDER=openai
OPENAI_MODEL=<production-openai-model>
ANTHROPIC_MODEL=<production-anthropic-model>
AI_CONFIDENCE_THRESHOLD=0.90
DOCUMENT_TEXT_EXTRACTION_PROVIDER=textract
AWS_REGION=us-east-2
TEXTRACT_S3_PREFIX=velvet-elves/textract-input
TEXTRACT_OCR_ONLY_MODE=true
TEXTRACT_FEATURE_TYPES=FORMS,TABLES,QUERIES,SIGNATURES,LAYOUT
TEXTRACT_POLL_INTERVAL_SECONDS=2
TEXTRACT_TIMEOUT_SECONDS=240
TEXTRACT_DELETE_SOURCE_AFTER_PROCESSING=true
TEXTRACT_MAX_CHARS=60000
PACKET_PARSE_TEXTRACT_CONCURRENCY=3
MICROSOFT_TENANT=common
GMAIL_WATCH_LABEL_IDS=INBOX
GMAIL_WATCH_LABEL_FILTER_BEHAVIOR=INCLUDE
COMMUNICATION_RETENTION_DAYS=730
DOCUSIGN_SCOPES=signature
VE_MULTI_WORKSPACE_V1=true
```

Recommended secret values:

```text
APP_SECRET_KEY
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_JWT_SECRET
SUPABASE_DB_URL
ENCRYPTION_KEY
OPENAI_API_KEY
ANTHROPIC_API_KEY
TEXTRACT_S3_BUCKET
SENDGRID_API_KEY
INVITE_EMAIL_SENDER
INVITE_EMAIL_SENDER_NAME
DOCUSIGN_INTEGRATION_KEY
DOCUSIGN_SECRET_KEY
DOCUSIGN_OAUTH_BASE_URL
DOCUSIGN_REDIRECT_URI
DOCUSIGN_WEBHOOK_SECRET
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GMAIL_REDIRECT_URI
GOOGLE_CALENDAR_REDIRECT_URI
GMAIL_PUBSUB_TOPIC_NAME
PUBSUB_PUSH_AUDIENCE
PUBSUB_PUSH_SERVICE_ACCOUNT_EMAIL
MICROSOFT_CLIENT_ID
MICROSOFT_CLIENT_SECRET
OUTLOOK_REDIRECT_URI
OUTLOOK_CALENDAR_REDIRECT_URI
EMAIL_WEBHOOK_SECRET
EMAIL_WEBHOOK_PUBLIC_BASE_URL
STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_CONNECT_PLATFORM_ACCOUNT_ID
```

Use one JSON secret for the backend:

```powershell
$BACKEND_SECRET_ARN = aws secretsmanager create-secret `
  --name $BACKEND_SECRET_NAME `
  --description "Velvet Elves $ENV_NAME backend runtime secrets" `
  --secret-string file://aws-deploy-work/backend-$ENV_NAME-secrets.json `
  --region $REGION `
  --query ARN --output text
```

`backend-$ENV_NAME-secrets.json` should be created locally from the matching environment `.env` and never committed.

Example shape:

```json
{
  "APP_SECRET_KEY": "replace-me",
  "SUPABASE_URL": "replace-me",
  "SUPABASE_ANON_KEY": "replace-me",
  "SUPABASE_SERVICE_ROLE_KEY": "replace-me",
  "SUPABASE_JWT_SECRET": "replace-me",
  "SUPABASE_DB_URL": "replace-me",
  "ENCRYPTION_KEY": "replace-me",
  "OPENAI_API_KEY": "replace-me",
  "ANTHROPIC_API_KEY": "replace-me",
  "TEXTRACT_S3_BUCKET": "replace-me",
  "STRIPE_SECRET_KEY": "replace-me"
}
```

If the secret already exists, update it instead of creating a second secret:

```powershell
$BACKEND_SECRET_ARN = aws secretsmanager describe-secret `
  --secret-id $BACKEND_SECRET_NAME `
  --region $REGION `
  --query ARN --output text

aws secretsmanager put-secret-value `
  --secret-id $BACKEND_SECRET_ARN `
  --secret-string file://aws-deploy-work/backend-$ENV_NAME-secrets.json `
  --region $REGION
```

Important ECS behavior:

- A Secrets Manager value change is not picked up by already-running tasks. Force a new ECS deployment after secret rotation.
- A plain task-definition `environment` value change is not picked up by force deployment alone. Register a new task definition revision, then update the ECS service to that revision.
- In task definitions, reference JSON keys with the full secret ARN returned by AWS, for example `<backend-secret-arn>:APP_SECRET_KEY::`. Do not hand-type an ARN that omits the random suffix AWS appends to Secrets Manager ARNs.
- JSON-key secret references require a supported Fargate platform version. Use `platform-version LATEST` or pin a version that supports Secrets Manager JSON key injection.

### 7.2 IAM Roles

Create two ECS IAM roles.

1. Task execution role:
   - Used by ECS/Fargate to pull from ECR, publish logs, and fetch Secrets Manager values.
   - Attach `arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy`.
   - Add `secretsmanager:GetSecretValue` for the exact `$BACKEND_SECRET_ARN`.
   - Add `kms:Decrypt` if the secret uses a customer-managed KMS key.

2. Task role:
   - Used by application code inside the FastAPI container.
   - Grant only the AWS calls the app itself performs:
     - `textract:StartDocumentAnalysis`
     - `textract:GetDocumentAnalysis`
     - `textract:StartDocumentTextDetection`
     - `textract:GetDocumentTextDetection`
     - `s3:GetObject`
     - `s3:PutObject`
     - `s3:DeleteObject`
     - `s3:GetObjectAttributes`
     - `s3:ListBucket` on the configured Textract bucket/prefix.

Trust policy for both roles:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Create `aws-deploy-work\ecs-execution-secrets-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "<backend-secret-arn>"
    }
  ]
}
```

If the backend secret uses a customer-managed KMS key, add a scoped `kms:Decrypt` statement for that key.

Create `aws-deploy-work\backend-textract-s3-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "textract:StartDocumentAnalysis",
        "textract:GetDocumentAnalysis",
        "textract:StartDocumentTextDetection",
        "textract:GetDocumentTextDetection"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::<textract-s3-bucket>",
      "Condition": {
        "StringLike": {
          "s3:prefix": [
            "velvet-elves/textract-input",
            "velvet-elves/textract-input/*"
          ]
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:GetObjectAttributes"
      ],
      "Resource": "arn:aws:s3:::<textract-s3-bucket>/velvet-elves/textract-input/*"
    }
  ]
}
```

Adjust the S3 prefix if `TEXTRACT_S3_PREFIX` is different. If the Textract bucket uses SSE-KMS, add the minimum required `kms:Decrypt`, `kms:Encrypt`, and `kms:GenerateDataKey` permissions for that bucket key.

Create roles:

```powershell
aws iam create-role `
  --role-name "$NAME_PREFIX-ecs-execution-role" `
  --assume-role-policy-document file://aws-deploy-work/ecs-task-trust-policy.json

aws iam attach-role-policy `
  --role-name "$NAME_PREFIX-ecs-execution-role" `
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

aws iam create-role `
  --role-name "$NAME_PREFIX-backend-task-role" `
  --assume-role-policy-document file://aws-deploy-work/ecs-task-trust-policy.json
```

Create and attach inline policies:

```powershell
aws iam put-role-policy `
  --role-name "$NAME_PREFIX-ecs-execution-role" `
  --policy-name "$NAME_PREFIX-read-backend-secrets" `
  --policy-document file://aws-deploy-work/ecs-execution-secrets-policy.json

aws iam put-role-policy `
  --role-name "$NAME_PREFIX-backend-task-role" `
  --policy-name "$NAME_PREFIX-textract-s3-policy" `
  --policy-document file://aws-deploy-work/backend-textract-s3-policy.json
```

If ECS Exec is required for production break-glass debugging, configure it deliberately before adding `--enable-execute-command` to the service:

- Add these actions to the backend task role: `ssmmessages:CreateControlChannel`, `ssmmessages:CreateDataChannel`, `ssmmessages:OpenControlChannel`, and `ssmmessages:OpenDataChannel`.
- Ensure the operator IAM principal is allowed to call `ecs:ExecuteCommand`.
- Ensure private tasks can reach Systems Manager Session Manager. With NAT this works through normal outbound internet access; without NAT, create the `ssmmessages` interface VPC endpoint.
- Decide whether command session logging is required and configure ECS Exec logging/KMS accordingly.

Do not enable ECS Exec by default if these prerequisites are not configured.

### 7.3 Build and Push Backend Image to ECR

Manual first deploy:

```powershell
cd C:\Projects\velvet-elves-backend

aws ecr get-login-password --region $REGION |
  docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

$IMAGE_TAG = "manual-$(Get-Date -Format yyyyMMddHHmmss)"
$IMAGE_URI = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPOSITORY:$ENV_NAME-$IMAGE_TAG"

docker build -t velvet-elves-backend:$IMAGE_TAG .
docker tag velvet-elves-backend:$IMAGE_TAG $IMAGE_URI
docker push $IMAGE_URI
```

Also tag a deployment alias only after the image passes ECS smoke tests:

```powershell
docker tag velvet-elves-backend:$IMAGE_TAG "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPOSITORY:$ENV_NAME-latest"
docker push "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPOSITORY:$ENV_NAME-latest"
```

### 7.4 Create ALB Target Group and Listeners

Create target group:

```powershell
$TG_ARN = aws elbv2 create-target-group `
  --name "$NAME_PREFIX-api-tg" `
  --protocol HTTP `
  --port 8000 `
  --vpc-id $VPC_ID `
  --target-type ip `
  --health-check-protocol HTTP `
  --health-check-path /api/health `
  --health-check-interval-seconds 30 `
  --health-check-timeout-seconds 5 `
  --healthy-threshold-count 2 `
  --unhealthy-threshold-count 3 `
  --matcher HttpCode=200 `
  --region $REGION `
  --query "TargetGroups[0].TargetGroupArn" `
  --output text
```

Create ALB:

```powershell
$ALB_ARN = aws elbv2 create-load-balancer `
  --name "$NAME_PREFIX-api-alb" `
  --subnets $PUBLIC_SUBNET_1 $PUBLIC_SUBNET_2 `
  --security-groups $ALB_SG `
  --scheme internet-facing `
  --type application `
  --region $REGION `
  --query "LoadBalancers[0].LoadBalancerArn" `
  --output text

$ALB_DNS = aws elbv2 describe-load-balancers `
  --load-balancer-arns $ALB_ARN `
  --region $REGION `
  --query "LoadBalancers[0].DNSName" `
  --output text
```

Create HTTPS listener:

```powershell
aws elbv2 create-listener `
  --load-balancer-arn $ALB_ARN `
  --protocol HTTPS `
  --port 443 `
  --certificates CertificateArn=$API_CERT_ARN `
  --ssl-policy ELBSecurityPolicy-TLS13-1-2-2021-06 `
  --default-actions Type=forward,TargetGroupArn=$TG_ARN `
  --region $REGION
```

Create HTTP-to-HTTPS redirect listener:

```powershell
aws elbv2 create-listener `
  --load-balancer-arn $ALB_ARN `
  --protocol HTTP `
  --port 80 `
  --default-actions "Type=redirect,RedirectConfig={Protocol=HTTPS,Port=443,StatusCode=HTTP_301}" `
  --region $REGION
```

Recommended ALB/target group tuning for this app:

```powershell
aws elbv2 modify-load-balancer-attributes `
  --load-balancer-arn $ALB_ARN `
  --attributes Key=idle_timeout.timeout_seconds,Value=120 `
  --region $REGION

aws elbv2 modify-target-group-attributes `
  --target-group-arn $TG_ARN `
  --attributes Key=deregistration_delay.timeout_seconds,Value=30 `
  --region $REGION
```

Rationale:

- Document uploads and OCR-adjacent requests can be slower than a tiny JSON API; a 120-second ALB idle timeout is a safer starting point than the default.
- A shorter deregistration delay makes rolling deploys and rollback faster while still allowing in-flight requests to drain.

Optional but recommended before production: add AWS WAF on the ALB or block production access to `/api/docs`, `/api/redoc`, and `/api/openapi.json` except from known admin IPs.

### 7.5 Register ECS Task Definition

Create `aws-deploy-work\backend-task-definition.json`.

Use `cpu` and `memory` based on testing. Recommended starting production value is `1024` CPU and `2048` MB memory, desired count `2`. If AI/document parsing requests are memory-heavy, increase to `2048` CPU and `4096` MB.

Skeleton:

```json
{
  "family": "velvet-elves-<env>-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/velvet-elves-<env>-ecs-execution-role",
  "taskRoleArn": "arn:aws:iam::<account-id>:role/velvet-elves-<env>-backend-task-role",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account-id>.dkr.ecr.<region>.amazonaws.com/velvet-elves/backend:<env>-<image-tag>",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        { "name": "APP_ENV", "value": "<staging-or-production>" },
        { "name": "APP_DEBUG", "value": "false" },
        { "name": "FRONTEND_URL", "value": "https://APP_DOMAIN" },
        { "name": "CORS_ORIGINS", "value": "https://APP_DOMAIN" },
        { "name": "DOCUMENT_TEXT_EXTRACTION_PROVIDER", "value": "textract" },
        { "name": "AWS_REGION", "value": "us-east-2" },
        { "name": "TEXTRACT_S3_PREFIX", "value": "velvet-elves/textract-input" },
        { "name": "TEXTRACT_OCR_ONLY_MODE", "value": "true" },
        { "name": "TEXTRACT_FEATURE_TYPES", "value": "FORMS,TABLES,QUERIES,SIGNATURES,LAYOUT" },
        { "name": "TEXTRACT_POLL_INTERVAL_SECONDS", "value": "2" },
        { "name": "TEXTRACT_TIMEOUT_SECONDS", "value": "240" },
        { "name": "TEXTRACT_DELETE_SOURCE_AFTER_PROCESSING", "value": "true" },
        { "name": "TEXTRACT_MAX_CHARS", "value": "60000" },
        { "name": "PACKET_PARSE_TEXTRACT_CONCURRENCY", "value": "3" },
        { "name": "COMMUNICATION_RETENTION_DAYS", "value": "730" },
        { "name": "MICROSOFT_TENANT", "value": "common" },
        { "name": "GMAIL_WATCH_LABEL_IDS", "value": "INBOX" },
        { "name": "GMAIL_WATCH_LABEL_FILTER_BEHAVIOR", "value": "INCLUDE" },
        { "name": "DOCUSIGN_SCOPES", "value": "signature" },
        { "name": "VE_MULTI_WORKSPACE_V1", "value": "true" }
      ],
      "secrets": [
        {
          "name": "APP_SECRET_KEY",
          "valueFrom": "<backend-secret-arn>:APP_SECRET_KEY::"
        },
        {
          "name": "SUPABASE_URL",
          "valueFrom": "<backend-secret-arn>:SUPABASE_URL::"
        },
        {
          "name": "SUPABASE_SERVICE_ROLE_KEY",
          "valueFrom": "<backend-secret-arn>:SUPABASE_SERVICE_ROLE_KEY::"
        },
        {
          "name": "SUPABASE_DB_URL",
          "valueFrom": "<backend-secret-arn>:SUPABASE_DB_URL::"
        },
        {
          "name": "ENCRYPTION_KEY",
          "valueFrom": "<backend-secret-arn>:ENCRYPTION_KEY::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/velvet-elves/<env>/backend",
          "awslogs-region": "us-east-2",
          "awslogs-stream-prefix": "api"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)\""],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 30
      }
    }
  ]
}
```

Notes:

- Include every secret required by `.env.example`, not only the abbreviated sample above.
- `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`, provider keys, webhook secrets, and Stripe secrets must also be mapped.
- Use the exact `APP_DOMAIN` and `API_DOMAIN` values when creating the real JSON.
- Replace `<backend-secret-arn>` with the full ARN returned by `aws secretsmanager describe-secret --secret-id $BACKEND_SECRET_NAME --query ARN --output text --region $REGION`.

Register:

```powershell
$TASK_DEF_ARN = aws ecs register-task-definition `
  --cli-input-json file://aws-deploy-work/backend-task-definition.json `
  --query "taskDefinition.taskDefinitionArn" `
  --output text `
  --region $REGION
```

### 7.6 Create ECS Cluster and Service

```powershell
aws ecs create-cluster --cluster-name $NAME_PREFIX --region $REGION
```

Create service:

```powershell
aws ecs create-service `
  --cluster $NAME_PREFIX `
  --service-name "$NAME_PREFIX-backend" `
  --task-definition $TASK_DEF_ARN `
  --desired-count 2 `
  --launch-type FARGATE `
  --platform-version LATEST `
  --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true},minimumHealthyPercent=100,maximumPercent=200" `
  --health-check-grace-period-seconds 60 `
  --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNET_1,$PRIVATE_SUBNET_2],securityGroups=[$ECS_SG],assignPublicIp=DISABLED}" `
  --load-balancers "targetGroupArn=$TG_ARN,containerName=api,containerPort=8000" `
  --region $REGION
```

Only append `--enable-execute-command` after the ECS Exec prerequisites in Section 7.2 are satisfied.

Wait for stability:

```powershell
aws ecs wait services-stable `
  --cluster $NAME_PREFIX `
  --services "$NAME_PREFIX-backend" `
  --region $REGION
```

Check task health:

```powershell
aws ecs describe-services `
  --cluster $NAME_PREFIX `
  --services "$NAME_PREFIX-backend" `
  --region $REGION `
  --query "services[0].{Running:runningCount,Desired:desiredCount,Deployments:deployments[*].{Status:status,Rollout:rolloutState,TaskDef:taskDefinition}}"
```

### 7.7 Backend DNS

After the ALB is healthy, create `API_DOMAIN` DNS.

Current GoDaddy DNS procedure:

1. In GoDaddy DNS for `velvetelves.com`, create or update a CNAME record:
   - Staging name: `api.stage`
   - Production name: `api`
   - Value: the ALB DNS name from `$ALB_DNS`.
2. Keep TTL low during cutover, for example `300` seconds.
3. Do not edit any mail records.
4. Do not edit `dev.velvetelves.com`.

Route 53 future example, after DNS hosting is migrated to Route 53:

```powershell
$HOSTED_ZONE_ID = "Zxxxxxxxx"
$ALB_ZONE_ID = aws elbv2 describe-load-balancers `
  --load-balancer-arns $ALB_ARN `
  --query "LoadBalancers[0].CanonicalHostedZoneId" `
  --output text
```

Create `aws-deploy-work\route53-api-alias.json`:

```json
{
  "Comment": "Point API domain to environment ALB",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "<api-domain>",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "<alb-canonical-hosted-zone-id>",
          "DNSName": "<alb-dns-name>",
          "EvaluateTargetHealth": true
        }
      }
    }
  ]
}
```

Apply:

```powershell
aws route53 change-resource-record-sets `
  --hosted-zone-id $HOSTED_ZONE_ID `
  --change-batch file://aws-deploy-work/route53-api-alias.json
```

### 7.8 Backend Smoke Tests

```powershell
curl.exe -fsS "https://$API_DOMAIN/api/health"
curl.exe -fsS "https://$API_DOMAIN/api/v1/health"
curl.exe -fsS "https://$API_DOMAIN/api/v1/health/ready"
curl.exe -I "https://$API_DOMAIN/api/docs"
```

Expected:

- `/api/health`: `200`.
- `/api/v1/health`: `200`.
- `/api/v1/health/ready`: `200` only when Supabase connectivity is healthy.
- `/api/docs`: decide whether this should be public, protected by WAF/IP, or blocked.

---

## 8. Phase 3 - Frontend on S3 and CloudFront

### 8.1 Create Private S3 Bucket

```powershell
aws s3api create-bucket `
  --bucket $FRONTEND_BUCKET `
  --region $REGION `
  --create-bucket-configuration LocationConstraint=$REGION

aws s3api put-public-access-block `
  --bucket $FRONTEND_BUCKET `
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

aws s3api put-bucket-encryption `
  --bucket $FRONTEND_BUCKET `
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

aws s3api put-bucket-versioning `
  --bucket $FRONTEND_BUCKET `
  --versioning-configuration Status=Enabled
```

If `$REGION` is `us-east-1`, omit `--create-bucket-configuration LocationConstraint=$REGION`; S3 rejects a location constraint for the classic `us-east-1` create-bucket call.

Do not enable S3 static website hosting for the frontend bucket. Use the S3 REST origin with CloudFront Origin Access Control so the bucket stays private.

### 8.2 Build Frontend for the Selected Environment

```powershell
cd C:\Projects\velvet-elves-frontend

$env:VITE_API_BASE_URL = "https://$API_DOMAIN"
$env:VITE_APP_ENV = if ($ENV_NAME -eq "prod") { "production" } else { "staging" }
$env:VITE_GOOGLE_MAPS_API_KEY = "<restricted-browser-key-if-used>"

npm ci
npm run build
```

Because Vite bakes these values into static files, changing `VITE_API_BASE_URL` later requires rebuilding and re-uploading the frontend.

### 8.3 Upload Frontend Assets to S3

Before uploading, decide whether source maps should be public. Vite does not emit production source maps by default, but if `dist` contains `*.map` files, do not rely on `aws s3 sync --exclude "*.map" --delete` to remove older maps. Files excluded from an S3 sync are also excluded from deletion.

If source maps should not be public, remove any old maps from the bucket first:

```powershell
aws s3 rm "s3://$FRONTEND_BUCKET" `
  --recursive `
  --exclude "*" `
  --include "*.map" `
  --region $REGION
```

Upload hashed assets with long cache. This command excludes `index.html` because the HTML shell must be uploaded with no-cache metadata.

Do not use `--delete` during the normal deploy sync. Deleting old hashed assets immediately can break users or CloudFront edge locations that still have the previous `index.html`. Clean old build assets later with an S3 lifecycle rule or a delayed cleanup after the rollback window.

```powershell
aws s3 sync .\dist "s3://$FRONTEND_BUCKET" `
  --exclude "index.html" `
  --exclude "*.map" `
  --cache-control "public,max-age=31536000,immutable" `
  --region $REGION
```

Re-upload `.mjs` files with an explicit JavaScript content type. This preserves the existing nginx production behavior that prevented the PDF worker from being served with the wrong MIME type:

```powershell
aws s3 cp .\dist "s3://$FRONTEND_BUCKET" `
  --recursive `
  --exclude "*" `
  --include "*.mjs" `
  --content-type "text/javascript" `
  --cache-control "public,max-age=31536000,immutable" `
  --region $REGION
```

Upload `index.html` with no-cache:

```powershell
aws s3 cp .\dist\index.html "s3://$FRONTEND_BUCKET/index.html" `
  --cache-control "no-cache,no-store,must-revalidate" `
  --content-type "text/html" `
  --region $REGION
```

Verify `.mjs` metadata:

```powershell
Get-ChildItem .\dist -Recurse -Filter *.mjs | ForEach-Object {
  $distRoot = (Resolve-Path .\dist).Path
  $key = $_.FullName.Substring($distRoot.Length + 1).Replace("\", "/")
  aws s3api head-object --bucket $FRONTEND_BUCKET --key $key --query "{Key:'$key',ContentType:ContentType,CacheControl:CacheControl}" --region $REGION
}
```

### 8.4 Create CloudFront Origin Access Control

Create `aws-deploy-work\frontend-oac.json`:

```json
{
  "Name": "velvet-elves-<env>-frontend-oac",
  "Description": "OAC for Velvet Elves <env> frontend S3 origin",
  "SigningProtocol": "sigv4",
  "SigningBehavior": "always",
  "OriginAccessControlOriginType": "s3"
}
```

Create OAC:

```powershell
$OAC_ID = aws cloudfront create-origin-access-control `
  --origin-access-control-config file://aws-deploy-work/frontend-oac.json `
  --query "OriginAccessControl.Id" `
  --output text
```

### 8.5 Create CloudFront Cache Policy

Create a custom cache policy that honors the `Cache-Control` metadata stored on S3 objects while keeping cookies, query strings, and arbitrary headers out of the cache key. This avoids the managed `CachingOptimized` policy's non-zero minimum TTL, which can cache `index.html` despite `no-cache` headers, and avoids the managed `UseOriginCacheControlHeaders` policy's unnecessary cookie-heavy cache key for this static SPA.

Create `aws-deploy-work\frontend-cache-policy-config.json`:

```json
{
  "Name": "velvet-elves-<env>-frontend-cache",
  "Comment": "Honor S3 Cache-Control for Vite assets and index.html",
  "DefaultTTL": 86400,
  "MaxTTL": 31536000,
  "MinTTL": 0,
  "ParametersInCacheKeyAndForwardedToOrigin": {
    "EnableAcceptEncodingGzip": true,
    "EnableAcceptEncodingBrotli": true,
    "HeadersConfig": {
      "HeaderBehavior": "none"
    },
    "CookiesConfig": {
      "CookieBehavior": "none"
    },
    "QueryStringsConfig": {
      "QueryStringBehavior": "none"
    }
  }
}
```

Create the cache policy:

```powershell
$FRONTEND_CACHE_POLICY_ID = aws cloudfront create-cache-policy `
  --cache-policy-config file://aws-deploy-work/frontend-cache-policy-config.json `
  --query "CachePolicy.Id" `
  --output text
```

If the policy already exists, look it up instead of creating a duplicate:

```powershell
$FRONTEND_CACHE_POLICY_ID = aws cloudfront list-cache-policies `
  --type custom `
  --query "CachePolicyList.Items[?CachePolicy.CachePolicyConfig.Name=='velvet-elves-$ENV_NAME-frontend-cache'].CachePolicy.Id | [0]" `
  --output text
```

### 8.6 Create CloudFront SPA Rewrite Function

Do not use distribution-wide `403`/`404` custom error responses as the primary SPA fallback. That common shortcut makes missing assets under `/assets/` return `index.html`, which can cause JavaScript module and PDF-worker failures that are hard to diagnose.

Use a viewer-request CloudFront Function to rewrite only route-like URLs to `/index.html`, while leaving real asset requests untouched.

Create `aws-deploy-work\spa-rewrite.js`:

```javascript
function handler(event) {
  var request = event.request;
  var uri = request.uri;

  if (uri === '/assets' || uri.indexOf('/assets/') === 0) {
    return request;
  }

  var lastSegment = uri.substring(uri.lastIndexOf('/') + 1);
  var hasExtension = lastSegment.indexOf('.') !== -1;

  if (!hasExtension) {
    request.uri = '/index.html';
  }

  return request;
}
```

Create and publish the function:

```powershell
aws cloudfront create-function `
  --name "$NAME_PREFIX-spa-rewrite" `
  --function-config Comment="Velvet Elves SPA route rewrite",Runtime=cloudfront-js-2.0 `
  --function-code fileb://aws-deploy-work/spa-rewrite.js

$SPA_FUNCTION_ETAG = aws cloudfront describe-function `
  --name "$NAME_PREFIX-spa-rewrite" `
  --stage DEVELOPMENT `
  --query ETag `
  --output text

aws cloudfront publish-function `
  --name "$NAME_PREFIX-spa-rewrite" `
  --if-match $SPA_FUNCTION_ETAG

$SPA_FUNCTION_ARN = aws cloudfront describe-function `
  --name "$NAME_PREFIX-spa-rewrite" `
  --stage LIVE `
  --query "FunctionSummary.FunctionMetadata.FunctionARN" `
  --output text
```

If the function already exists, update the DEVELOPMENT stage, publish it, and then use the LIVE ARN:

```powershell
$SPA_FUNCTION_ETAG = aws cloudfront describe-function `
  --name "$NAME_PREFIX-spa-rewrite" `
  --stage DEVELOPMENT `
  --query ETag `
  --output text

aws cloudfront update-function `
  --name "$NAME_PREFIX-spa-rewrite" `
  --if-match $SPA_FUNCTION_ETAG `
  --function-config Comment="Velvet Elves SPA route rewrite",Runtime=cloudfront-js-2.0 `
  --function-code fileb://aws-deploy-work/spa-rewrite.js

$SPA_FUNCTION_ETAG = aws cloudfront describe-function `
  --name "$NAME_PREFIX-spa-rewrite" `
  --stage DEVELOPMENT `
  --query ETag `
  --output text

aws cloudfront publish-function `
  --name "$NAME_PREFIX-spa-rewrite" `
  --if-match $SPA_FUNCTION_ETAG

$SPA_FUNCTION_ARN = aws cloudfront describe-function `
  --name "$NAME_PREFIX-spa-rewrite" `
  --stage LIVE `
  --query "FunctionSummary.FunctionMetadata.FunctionARN" `
  --output text
```

### 8.7 Create CloudFront Distribution

Create a CloudFront distribution JSON with:

- Alternate domain name: `APP_DOMAIN`.
- Viewer certificate: `$APP_CERT_ARN` from ACM in `us-east-1`.
- Origin domain: `$FRONTEND_BUCKET.s3.$REGION.amazonaws.com`.
- Origin access control ID: `$OAC_ID`.
- Default root object: `index.html`.
- Cache policy ID: `$FRONTEND_CACHE_POLICY_ID`.
- Viewer-request function ARN: `$SPA_FUNCTION_ARN`.
- Viewer protocol policy: redirect HTTP to HTTPS.
- Allowed methods: `GET`, `HEAD`.
- Compress objects automatically.
- Response headers policy: use the managed CloudFront `SecurityHeadersPolicy` (`67f7725c-6f97-4210-82d7-5512b31e9d03`) unless testing shows it conflicts with legitimate embedding requirements.

The CloudFront Function is what makes SPA deep links such as `/transactions/active` work. Missing assets should still return a real `403`/`404`, not the HTML shell.

Create `aws-deploy-work\cloudfront-frontend-distribution.json`:

```json
{
  "CallerReference": "velvet-elves-<env>-frontend-<unique-timestamp>",
  "Aliases": {
    "Quantity": 1,
    "Items": ["<app-domain>"]
  },
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "velvet-elves-<env>-frontend-s3",
        "DomainName": "velvet-elves-<env>-frontend-<account-id>.s3.us-east-2.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        },
        "OriginAccessControlId": "<oac-id>"
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "velvet-elves-<env>-frontend-s3",
    "TrustedSigners": {
      "Enabled": false,
      "Quantity": 0
    },
    "TrustedKeyGroups": {
      "Enabled": false,
      "Quantity": 0
    },
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "Compress": true,
    "CachePolicyId": "<frontend-cache-policy-id>",
    "ResponseHeadersPolicyId": "67f7725c-6f97-4210-82d7-5512b31e9d03",
    "FunctionAssociations": {
      "Quantity": 1,
      "Items": [
        {
          "FunctionARN": "<spa-function-live-arn>",
          "EventType": "viewer-request"
        }
      ]
    }
  },
  "CustomErrorResponses": {
    "Quantity": 0
  },
  "Comment": "Velvet Elves <env> frontend",
  "Enabled": true,
  "ViewerCertificate": {
    "ACMCertificateArn": "<us-east-1-acm-cert-arn>",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021"
  },
  "PriceClass": "PriceClass_100",
  "HttpVersion": "http2and3",
  "IsIPV6Enabled": true,
  "Restrictions": {
    "GeoRestriction": {
      "RestrictionType": "none",
      "Quantity": 0
    }
  }
}
```

Create distribution:

```powershell
$CF_DIST_ID = aws cloudfront create-distribution `
  --distribution-config file://aws-deploy-work/cloudfront-frontend-distribution.json `
  --query "Distribution.Id" `
  --output text

$CF_DOMAIN = aws cloudfront get-distribution `
  --id $CF_DIST_ID `
  --query "Distribution.DomainName" `
  --output text
```

### 8.8 Add S3 Bucket Policy for CloudFront OAC

After the distribution exists, grant CloudFront access to the S3 bucket.

Create `aws-deploy-work\frontend-bucket-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipalReadOnly",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::velvet-elves-<env>-frontend-<account-id>/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::<account-id>:distribution/<distribution-id>"
        }
      }
    }
  ]
}
```

Apply:

```powershell
aws s3api put-bucket-policy `
  --bucket $FRONTEND_BUCKET `
  --policy file://aws-deploy-work/frontend-bucket-policy.json `
  --region $REGION
```

### 8.9 Frontend DNS

Current GoDaddy DNS procedure:

1. In GoDaddy DNS for `velvetelves.com`, create or update a CNAME record:
   - Staging name: `app.stage`
   - Production name: `app`
   - Value: the CloudFront distribution domain name from `$CF_DOMAIN`.
2. Keep TTL low during cutover, for example `300` seconds.
3. Do not edit `velvetelves.com`, `help.velvetelves.com`, `help.stage.velvetelves.com`, company email records, or `dev.velvetelves.com` as part of the product frontend cutover.
4. If the marketing site later moves to CloudFront while DNS remains in GoDaddy, handle the apex `velvetelves.com` separately because a normal DNS CNAME cannot be used at the zone apex.

Route 53 future example, after DNS hosting is migrated to Route 53:

```powershell
aws route53 change-resource-record-sets `
  --hosted-zone-id $HOSTED_ZONE_ID `
  --change-batch file://aws-deploy-work/route53-app-alias.json
```

CloudFront hosted zone ID is globally `Z2FDTNDATAQYW2` for Route 53 alias records.

`route53-app-alias.json`:

```json
{
  "Comment": "Point frontend domain to CloudFront",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "<app-domain>",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z2FDTNDATAQYW2",
          "DNSName": "<cloudfront-domain-name>",
          "EvaluateTargetHealth": false
        }
      }
    }
  ]
}
```

### 8.10 CloudFront Invalidation

Because Vite asset filenames are hashed, avoid invalidating everything on normal deploys. Invalidate root and `index.html`.

```powershell
aws cloudfront create-invalidation `
  --distribution-id $CF_DIST_ID `
  --paths "/" "/index.html"
```

### 8.11 Frontend Smoke Tests

```powershell
curl.exe -I "https://$APP_DOMAIN/"
curl.exe -I "https://$APP_DOMAIN/transactions/active"
curl.exe -I "https://$APP_DOMAIN/transactions/active/"
curl.exe -I "https://$APP_DOMAIN/assets/<known-mjs-file>.mjs"
curl.exe -I "https://$APP_DOMAIN/assets/definitely-missing-file.mjs"
```

Manual browser checks:

- Load `/login`.
- Hard-refresh a deep link such as `/transactions/active`.
- Confirm API calls go to `https://API_DOMAIN`.
- Confirm no mixed-content errors.
- Confirm PDF viewer still loads worker `.mjs` files.
- Confirm the intentionally missing asset returns a real `403` or `404`, not `200 text/html`.
- Confirm Google Maps autocomplete works if `VITE_GOOGLE_MAPS_API_KEY` is configured.

---

## 9. Phase 4 - Environment Callback and Webhook Mapping

When moving domains, callbacks and webhooks are the easiest place to lose production behavior. Use this checklist.

Run this checklist twice:

- Staging after `main` deploys, using `STAGE_APP_DOMAIN`, `STAGE_API_DOMAIN`, staging Supabase, and sandbox/test provider credentials where available.
- Production after `prod` deploys, using `PROD_APP_DOMAIN`, `PROD_API_DOMAIN`, production Supabase, and production provider credentials.

### 9.1 Backend Environment Values

Set these backend values for the ECS environment being deployed:

```text
FRONTEND_URL=https://APP_DOMAIN
CORS_ORIGINS=https://APP_DOMAIN
DOCUSIGN_REDIRECT_URI=https://API_DOMAIN/api/v1/integrations/docusign/callback
GMAIL_REDIRECT_URI=https://API_DOMAIN/api/v1/integrations/gmail/callback
OUTLOOK_REDIRECT_URI=https://API_DOMAIN/api/v1/integrations/outlook/callback
GOOGLE_CALENDAR_REDIRECT_URI=https://API_DOMAIN/api/v1/calendar/google/callback
OUTLOOK_CALENDAR_REDIRECT_URI=https://API_DOMAIN/api/v1/calendar/outlook/callback
EMAIL_WEBHOOK_PUBLIC_BASE_URL=https://API_DOMAIN
PUBSUB_PUSH_AUDIENCE=https://API_DOMAIN/api/v1/integrations/email/webhook/gmail
```

If tenant subdomains are used later, add each allowed frontend origin to `CORS_ORIGINS` or move to a controlled dynamic-origin strategy in a future source-code change.

### 9.2 Supabase Auth

Update the matching Supabase project:

- Site URL: `https://APP_DOMAIN`.
- Redirect URLs:
  - `https://APP_DOMAIN/auth/callback`
  - `https://APP_DOMAIN/login`
  - Any tenant/custom-domain URLs already supported by the app.

This is not an AWS CLI action, but it is mandatory for auth links, password reset links, and invite flows.

### 9.3 Google Gmail OAuth

Register:

```text
https://API_DOMAIN/api/v1/integrations/gmail/callback
```

Inbound Gmail Pub/Sub push endpoint:

```text
https://API_DOMAIN/api/v1/integrations/email/webhook/gmail?user_id=<VELVET_ELVES_USER_ID>
```

Confirm:

- `GMAIL_PUBSUB_TOPIC_NAME` is set to the production Google Cloud topic.
- Gmail service account has publisher rights on the topic.
- Pub/Sub push authentication aligns with the backend's validation strategy.
- `PUBSUB_PUSH_AUDIENCE` matches the production push endpoint.

### 9.4 Microsoft Outlook OAuth and Graph Webhooks

Register:

```text
https://API_DOMAIN/api/v1/integrations/outlook/callback
```

Microsoft Graph notification endpoint:

```text
https://API_DOMAIN/api/v1/integrations/email/webhook/outlook?user_id=<VELVET_ELVES_USER_ID>
```

Confirm:

- The endpoint is public HTTPS.
- The backend responds to validation token probes.
- `EMAIL_WEBHOOK_SECRET` is set.
- Existing Outlook subscriptions may need to be renewed or recreated after domain cutover.

### 9.5 Google and Outlook Calendar OAuth

Register:

```text
https://API_DOMAIN/api/v1/calendar/google/callback
https://API_DOMAIN/api/v1/calendar/outlook/callback
```

Confirm:

- `GOOGLE_CALENDAR_REDIRECT_URI` is set.
- `OUTLOOK_CALENDAR_REDIRECT_URI` is set.

### 9.6 DocuSign

Register OAuth callback:

```text
https://API_DOMAIN/api/v1/integrations/docusign/callback
```

Register DocuSign Connect webhook:

```text
https://API_DOMAIN/api/v1/esign/webhooks/docusign
```

Confirm:

- `DOCUSIGN_OAUTH_BASE_URL` is sandbox or production as intended.
- `DOCUSIGN_WEBHOOK_SECRET` matches the DocuSign Connect HMAC key.
- Production DocuSign go-live/promotion is complete before using production envelopes.

### 9.7 Stripe

Register webhook:

```text
https://API_DOMAIN/api/v1/webhooks/stripe
```

Production events to include, based on current project docs:

```text
checkout.session.completed
payment_intent.succeeded
charge.refunded
refund.updated
```

Also include any commission-payout events needed by the older payments flow if it is enabled.

Confirm:

- `STRIPE_SECRET_KEY` is production or test as intended.
- `STRIPE_PUBLISHABLE_KEY` matches the same Stripe mode.
- `STRIPE_WEBHOOK_SECRET` is from the production webhook endpoint, not from `stripe listen`.
- Feature flags or platform billing settings are correct in the database.

### 9.8 SendGrid

Confirm:

- `SENDGRID_API_KEY` is production.
- `INVITE_EMAIL_SENDER` is a verified sender/domain.
- Supabase custom SMTP production settings still point to the intended SendGrid identity if Supabase Auth emails are used.

---

## 10. Phase 5 - CI/CD Changes To Make Later

This plan does not change source code or workflow files. When implementation begins, update CI/CD in a separate task.

### 10.1 Backend CI/CD Target State

Keep existing PR gates:

- Python setup.
- `pip install -r requirements.txt`.
- `ruff check .`.
- migration version validation.
- `pytest -q`.
- Docker build check.

Change deploy from GHCR plus SSH plus Docker Compose to two branch-specific ECS deploy lanes:

| Branch | GitHub environment | ECS target | Image aliases | Smoke-test domains |
| --- | --- | --- | --- | --- |
| `main` | `staging` | `velvet-elves-stage` / `velvet-elves-stage-backend` | `main-<sha>`, `stage-latest` | `STAGE_API_DOMAIN` |
| `prod` | `production` | `velvet-elves-prod` / `velvet-elves-prod-backend` | `prod-<sha>`, `prod-latest` | `PROD_API_DOMAIN` |

Each branch-specific deploy should:

1. Build Docker image.
2. Login to ECR.
3. Push image to ECR with immutable tag `<branch>-${GITHUB_SHA}` and an environment alias (`stage-latest` or `prod-latest`).
4. Run Supabase migrations against the matching environment database.
5. Ensure the matching Textract S3 bucket exists and has private/encrypted/lifecycle settings.
6. Render or patch ECS task definition with the new image URI and environment-specific variables.
7. Register new task definition revision.
8. `aws ecs update-service --cluster <env-cluster> --service <env-service> --task-definition <new-task-def>`.
9. `aws ecs wait services-stable`.
10. Smoke test:
    - `https://<env-api-domain>/api/health`
    - `https://<env-api-domain>/api/v1/health/ready`

GitHub Actions should use AWS OIDC, not long-lived AWS access keys.

Keep the migration database URL as a deployment secret, not an ECS runtime environment variable. Use separate GitHub environment secrets for staging and production, even if the secret key has the same name in each environment. If you introduce a clearer `SUPABASE_MIGRATION_DB_URL`, update the workflow and manual runbooks together so operators do not accidentally run migrations against the application's runtime pooler URL.

Required workflow trigger change:

```yaml
on:
  pull_request:
    branches: [main, prod]
  push:
    branches: [main, prod]
```

The deploy jobs must select environment-specific values from `github.ref_name`:

```text
main -> ENV_NAME=stage, GitHub environment=staging, APP_DOMAIN=STAGE_APP_DOMAIN, API_DOMAIN=STAGE_API_DOMAIN
prod -> ENV_NAME=prod, GitHub environment=production, APP_DOMAIN=PROD_APP_DOMAIN, API_DOMAIN=PROD_API_DOMAIN
```

### 10.2 Backend Manual Deploy Command Sequence

Manual release sequence until CI/CD is updated:

```powershell
# 1. Build and push image
cd C:\Projects\velvet-elves-backend
$IMAGE_TAG = "$(git rev-parse --short HEAD)-$(Get-Date -Format yyyyMMddHHmmss)"
$IMAGE_URI = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPOSITORY:$ENV_NAME-$IMAGE_TAG"
docker build -t velvet-elves-backend:$IMAGE_TAG .
docker tag velvet-elves-backend:$IMAGE_TAG $IMAGE_URI
docker push $IMAGE_URI

# 2. Apply Supabase migrations before shifting traffic.
# Stop here if migrations fail.
$env:SUPABASE_MIGRATION_DB_URL = "<matching-environment-supabase-migration-db-url>"
supabase db push --include-all --yes --db-url "$env:SUPABASE_MIGRATION_DB_URL"

# 3. Confirm the Textract S3 bucket is private, encrypted, and has cleanup lifecycle.
# Run the existing deploy/ensure-textract-s3.sh from Git Bash/WSL, or execute equivalent AWS CLI checks.

# 4. Update task definition JSON image field manually or via jq in a non-Windows shell.
# 5. Register task definition.
$TASK_DEF_ARN = aws ecs register-task-definition --cli-input-json file://aws-deploy-work/backend-task-definition.json --query "taskDefinition.taskDefinitionArn" --output text --region $REGION

# 6. Update service.
aws ecs update-service --cluster $NAME_PREFIX --service "$NAME_PREFIX-backend" --task-definition $TASK_DEF_ARN --region $REGION
aws ecs wait services-stable --cluster $NAME_PREFIX --services "$NAME_PREFIX-backend" --region $REGION

# 7. Smoke test.
curl.exe -fsS "https://$API_DOMAIN/api/health"
curl.exe -fsS "https://$API_DOMAIN/api/v1/health/ready"
```

### 10.3 Frontend CI/CD Target State

Keep existing PR gates:

- `npm ci`.
- `npm run lint`.
- `npx tsc --noEmit`.
- `npm run build`.

Change frontend deploy from GHCR plus SSH plus Docker Compose to S3/CloudFront per branch:

1. Build with environment-specific Vite variables:
   - `main`: `VITE_API_BASE_URL=https://STAGE_API_DOMAIN`, `VITE_APP_ENV=staging`
   - `prod`: `VITE_API_BASE_URL=https://PROD_API_DOMAIN`, `VITE_APP_ENV=production`
   - `VITE_GOOGLE_MAPS_API_KEY=<restricted key if used>`
2. Sync `dist` to the matching environment S3 bucket with cache-control rules.
3. Ensure `.mjs` assets have JavaScript content type.
4. Invalidate `/` and `/index.html` in the matching CloudFront distribution.
5. Smoke test the matching `APP_DOMAIN` and one deep link.

### 10.4 Frontend Manual Deploy Command Sequence

```powershell
cd C:\Projects\velvet-elves-frontend

$env:VITE_API_BASE_URL = "https://$API_DOMAIN"
$env:VITE_APP_ENV = if ($ENV_NAME -eq "prod") { "production" } else { "staging" }
$env:VITE_GOOGLE_MAPS_API_KEY = "<restricted-browser-key-if-used>"

npm ci
npm run build

# Optional if source maps must not be public and old maps might exist.
aws s3 rm "s3://$FRONTEND_BUCKET" `
  --recursive `
  --exclude "*" `
  --include "*.map" `
  --region $REGION

# Do not use --delete here; keep old hashed assets through the rollback window.
aws s3 sync .\dist "s3://$FRONTEND_BUCKET" `
  --exclude "index.html" `
  --exclude "*.map" `
  --cache-control "public,max-age=31536000,immutable" `
  --region $REGION

aws s3 cp .\dist "s3://$FRONTEND_BUCKET" `
  --recursive `
  --exclude "*" `
  --include "*.mjs" `
  --content-type "text/javascript" `
  --cache-control "public,max-age=31536000,immutable" `
  --region $REGION

aws s3 cp .\dist\index.html "s3://$FRONTEND_BUCKET/index.html" `
  --cache-control "no-cache,no-store,must-revalidate" `
  --content-type "text/html" `
  --region $REGION

aws cloudfront create-invalidation --distribution-id $CF_DIST_ID --paths "/" "/index.html"
```

### 10.5 Branch Protection and Promotion Rules

Configure GitHub branch protection before turning on the new deploy workflows:

| Branch | Protection rule |
| --- | --- |
| `develop` | Optional but recommended: require PRs for shared integration work and require backend/frontend CI where practical |
| `main` | Require PR, require backend/frontend CI, allow merge from `develop` and feature branches, deploy only to `staging` |
| `prod` | Require PR, require backend/frontend CI, require at least one approval, restrict direct pushes, promote only from `main`, deploy only to `production` |

Recommended production promotion:

First-time `prod` branch creation, after `main` is validated in staging:

```powershell
git checkout main
git pull --ff-only
git checkout -b prod
git push -u origin prod
```

Normal promotion:

```powershell
git checkout main
git pull --ff-only
git checkout prod
git pull --ff-only
git merge --ff-only main
git push origin prod
```

If `prod` cannot fast-forward from `main`, stop and reconcile with a PR. Do not create a unique production-only commit unless it is an emergency hotfix that will be merged back to `main` and `develop` immediately after production is stable.

---

## 11. Phase 6 - Staging Validation and Production Cutover Plan

### 11.1 Staging First From `main`

Before moving real users:

1. Merge `develop` into `main`.
2. Let the `main` branch deploy staging backend to `velvet-elves-stage`.
3. Let the `main` branch deploy staging frontend to the staging S3/CloudFront distribution.
4. Use `STAGE_API_DOMAIN` and `STAGE_APP_DOMAIN` for all staging checks.
5. Set staging backend `CORS_ORIGINS` to `https://STAGE_APP_DOMAIN`.
6. Configure staging callbacks/webhooks to staging or sandbox provider endpoints.
7. Keep `dev.velvetelves.com` unchanged.
8. Confirm staging marketing and help center DNS names are either unconfigured or intentionally pointed at their staging hosts.
9. Verify end-to-end on staging.
10. Record the exact commit SHA validated on `main`.

### 11.2 DNS TTL

At least 24 hours before cutover:

- Lower old frontend and API DNS TTLs to `300` seconds.
- In GoDaddy, lower only records involved in cutover.
- Confirm company email DNS records are unchanged and exported/screenshot before cutover.
- Confirm Route 53 is not the authoritative DNS provider yet unless a separate DNS migration has already been completed.

### 11.3 Production Promotion To `prod`

1. Announce maintenance window if needed.
2. Pause the old EC2 production deploy workflow.
3. Confirm no Supabase migration is currently running.
4. Promote the exact validated `main` commit to `prod`. Prefer a PR from `main` to `prod` or a fast-forward merge so production receives the same commit tested in staging.
5. Let the `prod` branch deploy production backend to `velvet-elves-prod`.
6. Let the `prod` branch deploy production frontend to the production S3/CloudFront distribution.
7. Update production backend secret/config:
   - `FRONTEND_URL=https://PROD_APP_DOMAIN`
   - `CORS_ORIGINS=https://PROD_APP_DOMAIN`
   - all production callback URLs using `PROD_API_DOMAIN`.
8. Apply the backend configuration update using the correct ECS mechanism:
   - If only Secrets Manager values changed, force a new deployment so the running tasks fetch the latest secret values.
   - If task-definition `environment` values, the image URI, log settings, or resource sizing changed, register a new task definition revision and update the service to that revision.

   Secret-only refresh:

   ```powershell
   $ENV_NAME = "prod"
   $NAME_PREFIX = "velvet-elves-prod"

   aws ecs update-service `
     --cluster $NAME_PREFIX `
     --service "$NAME_PREFIX-backend" `
     --force-new-deployment `
     --region $REGION
   ```

   Task-definition revision update:

   ```powershell
   $TASK_DEF_ARN = aws ecs register-task-definition `
     --cli-input-json file://aws-deploy-work/backend-task-definition.json `
     --query "taskDefinition.taskDefinitionArn" `
     --output text `
     --region $REGION

   aws ecs update-service `
     --cluster $NAME_PREFIX `
     --service "$NAME_PREFIX-backend" `
     --task-definition $TASK_DEF_ARN `
     --region $REGION
   ```

9. Wait for service stability.
10. Update DNS:
   - In GoDaddy, point `PROD_API_DOMAIN` CNAME to the production ALB DNS name.
   - In GoDaddy, point `PROD_APP_DOMAIN` CNAME to the production CloudFront domain name.
   - Do not change `PROD_MARKETING_DOMAIN`, `PROD_HELP_DOMAIN`, `dev.velvetelves.com`, or company email records during the app/API cutover.
11. Update external providers if not already done:
   - Supabase Auth.
   - Google/Microsoft OAuth.
   - Google Pub/Sub push subscription.
   - Microsoft Graph subscriptions.
   - DocuSign OAuth and Connect.
   - Stripe webhook.
12. Smoke test from a clean browser session.
13. Monitor logs and alarms for at least 2 hours after cutover.

### 11.4 Keep EC2 as Warm Rollback

Keep current EC2 infrastructure available for at least 7 days after cutover.

- Do not terminate EC2 immediately.
- Do not delete old DNS records immediately.
- Disable automatic EC2 deploys once ECS is serving production.
- After confidence window, stop EC2 instances before terminating them.
- Keep `dev.velvetelves.com` running until a separate replacement plan exists.

---

## 12. Rollback Plan

### 12.1 Backend Rollback

Preferred rollback if ECS is healthy but latest image is bad:

```powershell
aws ecs update-service `
  --cluster $NAME_PREFIX `
  --service "$NAME_PREFIX-backend" `
  --task-definition <previous-working-task-definition-arn> `
  --region $REGION

aws ecs wait services-stable `
  --cluster $NAME_PREFIX `
  --services "$NAME_PREFIX-backend" `
  --region $REGION
```

Fallback rollback if ECS/ALB stack is bad:

- Point `API_DOMAIN` DNS in GoDaddy back to the existing EC2 backend.
- Restore provider webhook URLs to the EC2 domain if the rollback will last more than a few minutes.
- Keep CORS compatible with the frontend domain during rollback.

Migration warning:

- If a Supabase migration was applied and is not backward-compatible with the old EC2 backend, DNS rollback may not be sufficient.
- For cutover week, prefer backward-compatible migrations only.

### 12.2 Frontend Rollback

Preferred rollback:

- Re-upload the previous `dist` artifact to S3.
- Invalidate `/` and `/index.html`.

Fallback rollback:

- Point `APP_DOMAIN` DNS in GoDaddy back to the EC2 frontend.

Important:

- If the frontend was built with a different `VITE_API_BASE_URL`, the rollback artifact must match the API domain currently in use.

### 12.3 Provider Callback Rollback

If rolling back domains:

- Stripe can temporarily keep both old and new webhook endpoints active.
- DocuSign Connect may need old URL restored.
- Google/Microsoft OAuth redirect URLs can usually contain both old and new URLs.
- Gmail Pub/Sub and Microsoft Graph subscriptions may need old push endpoints restored or recreated.
- Do not modify company email records during rollback unless the incident is specifically email-related.

---

## 13. Environment Validation Checklist

Run these checks on staging after every `main` deploy. Run the same checks on production after every `prod` deploy and before/after DNS cutover.

### 13.1 Infrastructure

- ECS service desired count equals running count.
- ECS tasks are spread across at least two Availability Zones.
- ALB target group has healthy targets.
- ALB HTTPS listener uses the correct certificate.
- ALB HTTP listener redirects to HTTPS.
- CloudWatch logs receive backend logs.
- No secrets are printed in logs.
- CloudFront distribution is deployed.
- S3 frontend bucket blocks public access.
- S3 frontend bucket policy only allows CloudFront OAC.
- CloudFront Function rewrites route-like URLs to `/index.html`.
- Missing asset URLs return real `403`/`404` responses instead of `index.html`.
- GoDaddy DNS records for app/API point to the intended staging or production AWS targets.
- Company email DNS records are unchanged and email delivery still works.
- `dev.velvetelves.com` remains unchanged.

### 13.2 Backend

- `GET https://API_DOMAIN/api/health` returns `200`.
- `GET https://API_DOMAIN/api/v1/health/ready` returns `200`.
- Swagger/OpenAPI exposure is intentionally allowed or intentionally blocked.
- Login succeeds.
- Authenticated API call succeeds with Supabase JWT.
- Tenant isolation still works.
- File upload succeeds.
- Document parsing can call Textract and clean up the temporary S3 object.
- AI parsing/suggestions can reach the configured AI provider.
- Email invite sends or produces the expected configured behavior.
- Stripe config endpoint returns the correct publishable key.

### 13.3 Frontend

- `https://APP_DOMAIN/` loads.
- `/login` loads on hard refresh.
- Deep link hard refresh works:
  - `/dashboard`
  - `/transactions/active`
  - `/settings`
- Frontend calls `https://API_DOMAIN`, not the old EC2 host.
- No CORS errors.
- No mixed content errors.
- PDF worker `.mjs` loads with JavaScript MIME type.
- Static assets have long cache headers.
- `index.html` is not aggressively cached.
- Marketing and help center domains resolve to their intended separate targets, if they are active for that environment.

### 13.4 User Flows

- Register/login/logout/password reset.
- Invite acceptance.
- Transaction create/edit.
- Document upload and document center view.
- AI wizard document parsing.
- Active Transactions filters/search/sort.
- Team management and user invite flows.
- Client portal access.
- Vendor portal scoped document access.
- DocuSign OAuth connect.
- DocuSign send/sign webhook updates document status.
- Gmail OAuth connect and send.
- Outlook OAuth connect and send.
- Gmail inbound webhook.
- Outlook inbound webhook.
- Calendar OAuth connect.
- Stripe Checkout and webhook reconciliation in test mode before live mode.

---

## 14. Monitoring and Alerts

Minimum production alarms. Create staging versions for lower-threshold smoke/early-warning coverage where cost is acceptable:

| Area | Alarm |
| --- | --- |
| ALB | 5xx count above threshold |
| ALB | Target response time p95 above threshold |
| ALB | Unhealthy target count greater than 0 |
| ECS | Running task count below desired count |
| ECS | CPU above 70 percent for 10 minutes |
| ECS | Memory above 80 percent for 10 minutes |
| ECS | Task stopped unexpectedly |
| CloudFront | 5xx error rate above threshold |
| CloudFront | 4xx error rate spike |
| Backend logs | Error keyword metric filter |
| Stripe | Webhook failures in Stripe dashboard |
| DocuSign | Connect delivery failures |

Useful AWS CLI checks:

```powershell
aws ecs describe-services --cluster $NAME_PREFIX --services "$NAME_PREFIX-backend" --region $REGION
aws elbv2 describe-target-health --target-group-arn $TG_ARN --region $REGION
aws logs tail $BACKEND_LOG_GROUP --follow --region $REGION
aws cloudfront get-distribution --id $CF_DIST_ID
```

---

## 15. Scaling and Capacity

Initial backend sizing:

- Staging: 1 task, `512` CPU, `1024` MB memory.
- Production starting point: 2 tasks, `1024` CPU, `2048` MB memory.
- Autoscale production between 2 and 6 tasks.

Target tracking:

```powershell
aws application-autoscaling register-scalable-target `
  --service-namespace ecs `
  --resource-id "service/$NAME_PREFIX/$NAME_PREFIX-backend" `
  --scalable-dimension ecs:service:DesiredCount `
  --min-capacity 2 `
  --max-capacity 6 `
  --region $REGION
```

CPU target policy example:

Save as `aws-deploy-work\ecs-cpu-scaling-policy.json`:

```json
{
  "TargetValue": 60.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
  },
  "ScaleOutCooldown": 60,
  "ScaleInCooldown": 180
}
```

Apply:

```powershell
aws application-autoscaling put-scaling-policy `
  --service-namespace ecs `
  --resource-id "service/$NAME_PREFIX/$NAME_PREFIX-backend" `
  --scalable-dimension ecs:service:DesiredCount `
  --policy-name "$NAME_PREFIX-backend-cpu60" `
  --policy-type TargetTrackingScaling `
  --target-tracking-scaling-policy-configuration file://aws-deploy-work/ecs-cpu-scaling-policy.json `
  --region $REGION
```

Memory target policy can be added at 70 percent after observing baseline memory.

Long-running AI/document parsing note:

- The current backend uses FastAPI background tasks in places.
- If production traffic grows or OCR/AI tasks become long-running, create a separate ECS worker service with SQS in a future architecture phase.
- Do not introduce that worker in the initial migration unless production tests show request latency or task reliability problems.

---

## 16. Security Hardening Checklist

Backend:

- ECS tasks run in private subnets.
- ECS task security group accepts port `8000` only from the ALB security group.
- ALB accepts public `80` and `443`; `80` redirects to `443`.
- Use exact CORS origins.
- Use Secrets Manager for sensitive values.
- Use task role for Textract/S3 access, not access keys in environment variables.
- Use least-privilege IAM resource ARNs for the Textract S3 bucket.
- Consider WAF managed rules on CloudFront and ALB.
- Consider IP restriction for `/api/docs`, `/api/redoc`, and `/api/openapi.json`.

Frontend:

- S3 bucket public access blocked.
- CloudFront OAC is the only read path to S3.
- CloudFront viewer protocol redirects HTTP to HTTPS.
- CloudFront certificate covers `APP_DOMAIN`.
- `VITE_GOOGLE_MAPS_API_KEY`, if used, is restricted by HTTP referrer to production frontend domains.

DNS and domain:

- GoDaddy account uses strong 2FA.
- Domain lock is enabled except during an intentional registrar transfer.
- Domain auto-renewal is enabled and payment method is current.
- GoDaddy account recovery email is secure and monitored.
- DNS changes are performed from an exported/screenshot baseline.
- Email records are protected from accidental edits during app/API changes.
- Route 53 migration is handled later as a separate project: migrate DNS hosting first, verify app/API/marketing/help/email, then transfer registrar only after DNS stability is proven.

Operational:

- Do not store production `.env` files on EC2 after migration unless retained for rollback.
- Rotate any secret that was broadly copied during migration.
- Use separate staging and production provider credentials where possible.
- Review CloudWatch logs for accidental PII exposure.

---

## 17. What Not To Change In This Migration

Keep this migration focused on infrastructure.

Do not change:

- FastAPI source code.
- React source code.
- Database schema except already planned migrations.
- Authentication model.
- Supabase RLS logic.
- Frontend route structure.
- Provider integration logic.

Only change source or workflows in a later implementation task if needed for:

- CI/CD deploy target changes.
- Runtime frontend configuration instead of build-time Vite variables.
- Worker queue extraction for long-running background jobs.
- Production-only disabling of docs routes inside FastAPI.

---

## 18. Acceptance Criteria

The migration is complete when:

- `develop` is local-only and does not automatically deploy to AWS.
- `main` deploys to the staging ECS/CloudFront stack only.
- `prod` deploys to the production ECS/CloudFront stack only.
- The production deployment is promoted from a staging-validated commit on `main`.
- Backend production traffic is served by ECS Fargate, not EC2.
- Frontend production traffic is served by CloudFront and private S3, not EC2.
- `STAGE_APP_DOMAIN` and `PROD_APP_DOMAIN` load the SPA and support hard-refresh deep links.
- `STAGE_API_DOMAIN` and `PROD_API_DOMAIN` serve backend health and authenticated APIs.
- `STAGE_MARKETING_DOMAIN`, `PROD_MARKETING_DOMAIN`, `STAGE_HELP_DOMAIN`, and `PROD_HELP_DOMAIN` are either intentionally configured to their separate services or explicitly documented as pending separate website/help-center work.
- `dev.velvetelves.com` remains unchanged and available.
- GoDaddy DNS records for app/API are correct, and company email DNS records remain intact.
- CORS is clean from each environment's frontend to its matching API.
- Supabase Auth login, password reset, and invite flows use the matching environment frontend domain.
- Textract-backed document parsing works from ECS using task-role credentials.
- Stripe webhooks reach ECS and verify signatures.
- DocuSign Connect reaches ECS and verifies HMAC.
- Gmail/Outlook OAuth callbacks use the ECS API domain.
- Gmail/Outlook inbound webhook flows work or have a documented provider-side follow-up.
- CloudWatch alarms are active.
- EC2 rollback is retained for the agreed confidence window, then decommissioned.

---

## 19. Official AWS References Checked

- Amazon ECR image push flow: https://docs.aws.amazon.com/AmazonECR/latest/userguide/docker-push-ecr-image.html
- ECS Secrets Manager environment variables: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html
- ECS task execution role: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html
- ECS task IAM role: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html
- ECS with Application Load Balancer: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/alb.html
- ALB HTTPS listener: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/create-https-listener.html
- ECS outbound networking for private subnets and NAT: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/networking-outbound.html
- ECS Exec: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-exec.html
- CloudFront OAC for private S3 origins: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html
- CloudFront certificate region requirement: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html
- CloudFront cache policies: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/controlling-the-cache-key.html
- CloudFront managed response headers policies: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-managed-response-headers-policies.html
- CloudFront Functions: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-functions.html
- CloudFront Function SPA URL rewrite example: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/example_cloudfront_functions_url_rewrite_single_page_apps_section.html
- CloudFront invalidations and versioned files: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html
- AWS CLI `s3 sync` options: https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html
- Route 53 supported DNS record types and alias behavior: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/ResourceRecordTypes.html
- Route 53 DNS migration for an existing domain: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/migrate-dns-domain-in-use.html
- Route 53 domain registration transfer process: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-transfer-to-route-53.html
