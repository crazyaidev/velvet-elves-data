# Velvet Elves CI/CD Pipeline Implementation Guidelines

Date: 2026-06-30

Status: Standard implementation guide for all Velvet Elves repositories.

Purpose:

- Define one consistent CI/CD model for the four Velvet Elves repositories.
- Preserve the branch promotion flow: `develop` -> `main` -> `prod`.
- Keep deployment metadata in GitHub Variables.
- Keep runtime secrets out of GitHub and in AWS-managed secret stores where applicable.
- Make staging and production deployment behavior predictable across backend, frontend, marketing, and help center projects.

Repositories covered:

```text
velvet-elves-frontend        Main product frontend
velvet-elves-backend         Backend API
velvet-elves-marketing-website   Marketing website
velvet-elves-help-center     Help center
```

---

## 1. Branch And Environment Model

All four repositories use the same branch model:

```text
develop  local development and feature integration
main     staging deployment branch
prod     production deployment branch
```

Promotion flow:

```text
develop -> main -> prod
```

Rules:

- `develop` is the working branch.
- Pull requests into `main` run CI checks only.
- Merging into `main` deploys to staging.
- Pull requests into `prod` run CI checks only.
- Merging into `prod` deploys to production.
- No automatic deployment should run from `develop`.
- Git operations are manual. The workflow should not merge, rebase, tag, or promote branches automatically.

Recommended pull request flow:

```text
feature/local work -> develop
develop -> main PR
main -> prod PR
```

---

## 2. Domain Model

Staging:

```text
stage.velvetelves.com            Staging marketing site
app.stage.velvetelves.com        Staging product frontend
api.stage.velvetelves.com        Staging backend API
help.stage.velvetelves.com       Staging help center
```

Production:

```text
velvetelves.com                  Production marketing site
app.velvetelves.com              Production product frontend
api.velvetelves.com              Production backend API
help.velvetelves.com             Production help center
```

Development server:

```text
dev.velvetelves.com              Existing development server, unchanged
```

`dev.velvetelves.com` must not be repointed or removed as part of staging or production CI/CD work.

---

## 3. Secrets And Variables Policy

This is the most important rule:

```text
GitHub Variables: deployment metadata only
AWS Secrets Manager or equivalent AWS secret store: runtime secrets
GitHub Secrets: avoid by default
```

### 3.1 GitHub Variables

Use GitHub Variables for non-secret deployment metadata, such as:

- AWS region
- AWS deploy role ARN
- ECR repository URI
- ECS cluster name
- ECS service name
- ECS task family
- S3 bucket name
- CloudFront distribution ID
- Public site origin URL
- Public API base URL
- Health check URL
- AWS Secrets Manager secret ID or path

These are identifiers and deployment targets. They are not application secrets.

### 3.2 AWS Secrets Manager

Use AWS Secrets Manager for backend runtime values, such as:

- `APP_SECRET_KEY`
- `ENCRYPTION_KEY`
- `SUPABASE_*`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `SENDGRID_API_KEY`
- `DOCUSIGN_*`
- `STRIPE_*`
- webhook secrets
- OAuth client secrets
- database URLs

The backend GitHub Actions workflow may read `SUPABASE_MIGRATION_DB_URL` from AWS Secrets Manager during deployment, mask it, and use it for migrations. It must not read that value from GitHub Secrets or GitHub Variables.

### 3.3 Static Frontend Build Variables

Frontend, marketing, and help center apps may need build-time variables such as:

```text
VITE_API_BASE_URL
VITE_HELP_API_BASE_URL
VITE_SUPABASE_URL
VITE_SUPABASE_ANON_KEY
```

Treat Vite variables as public. Anything included in a browser bundle can be viewed by users.

Rules:

- Store public build-time values in GitHub Variables.
- Do not store private API keys or service-role keys in static frontend builds.
- If a value must remain private, it belongs in the backend or AWS secret store, not in a Vite app.

### 3.4 GitHub Secrets

GitHub Secrets should not be the default place for this project.

Use GitHub Secrets only if there is a specific GitHub-native need that cannot be handled through GitHub Variables, OIDC, or AWS Secrets Manager.

Do not use fallback patterns like:

```yaml
${{ vars.X || secrets.X }}
```

That pattern weakens the contract and makes it unclear where the source of truth lives.

Correct pattern:

```yaml
${{ vars.STAGE_AWS_REGION }}
```

---

## 4. Standard Workflow Trigger Pattern

Every repository should use this trigger shape unless there is a deliberate exception:

```yaml
on:
  pull_request:
    branches: [main, prod]
  push:
    branches: [main, prod]
  workflow_dispatch:
```

Meaning:

- PR to `main`: validate code before staging.
- Push to `main`: deploy staging.
- PR to `prod`: validate code before production.
- Push to `prod`: deploy production.
- Manual dispatch: allow redeploy from `main` or `prod`.

Deploy jobs must be gated:

```yaml
if: (github.event_name == 'push' || github.event_name == 'workflow_dispatch') && (github.ref_name == 'main' || github.ref_name == 'prod')
```

CI jobs should be gated:

```yaml
if: github.event_name == 'pull_request'
```

---

## 5. Standard Permissions

Use GitHub OIDC to assume AWS roles. Do not store AWS access keys in GitHub.

Recommended workflow permissions:

```yaml
permissions:
  contents: read
  id-token: write
```

The AWS deploy role must trust the specific GitHub repository and branch pattern required for deployment.

Recommended role trust separation:

- Staging role can deploy from `main`.
- Production role can deploy from `prod`.
- Pull requests should not assume deploy roles.

### 5.1 AWS CLI Operator Preflight

Before creating or changing AWS resources, verify AWS CLI access from the exact
terminal, user, container, or automation context that will run the commands.

Run:

```powershell
whoami
aws --version
aws configure list
aws configure list-profiles
aws sts get-caller-identity --output json
```

Expected account:

```text
388482955098
```

Expected default region for current Velvet Elves resources:

```text
us-east-2
```

Important:

- A local desktop terminal may be logged in while a sandboxed shell, elevated shell, service account, container, or CI runner cannot read the same `~/.aws` files.
- If `aws configure list` shows no access key, no profile, and no region, do not assume AWS is unavailable. First check the shell identity and credential context.
- On Windows, compare `whoami`, `$env:USERPROFILE`, `$env:AWS_PROFILE`, `$env:AWS_REGION`, and `$env:AWS_DEFAULT_REGION`.
- If a command must run outside a restricted shell to read `~/.aws/config` or `~/.aws/credentials`, explicitly rerun the same read-only preflight there before making changes.
- GitHub Actions must not use local AWS CLI credentials. GitHub Actions uses OIDC and the deploy role configured in GitHub Variables.

If using a named AWS profile, either pass the profile explicitly:

```powershell
aws sts get-caller-identity --profile velvet-elves --output json
```

or set it for the current shell:

```powershell
$env:AWS_PROFILE = "velvet-elves"
aws sts get-caller-identity --output json
```

Do not proceed with AWS changes unless `aws sts get-caller-identity` returns
the expected account.

### 5.2 GitHub OIDC Deploy Role Verification

Every deploy role must trust only the intended repository and branch.

Staging static-site trust should be scoped to `main`:

```json
{
  "Effect": "Allow",
  "Principal": {
    "Federated": "arn:aws:iam::388482955098:oidc-provider/token.actions.githubusercontent.com"
  },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:velvetadmin/REPOSITORY_NAME:ref:refs/heads/main"
    }
  }
}
```

Production static-site trust should be scoped to `prod`:

```json
{
  "Effect": "Allow",
  "Principal": {
    "Federated": "arn:aws:iam::388482955098:oidc-provider/token.actions.githubusercontent.com"
  },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:velvetadmin/REPOSITORY_NAME:ref:refs/heads/prod"
    }
  }
}
```

Static-site deploy roles need these permissions for their own bucket and
CloudFront distribution:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListSiteBucket",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::SITE_BUCKET"
    },
    {
      "Sid": "WriteSiteObjects",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::SITE_BUCKET/*"
    },
    {
      "Sid": "InvalidateSiteDistribution",
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation",
        "cloudfront:GetInvalidation"
      ],
      "Resource": "arn:aws:cloudfront::388482955098:distribution/DISTRIBUTION_ID"
    }
  ]
}
```

`cloudfront:GetInvalidation` is required when the workflow waits for
invalidation completion. Without it, `aws cloudfront wait
invalidation-completed` can fail even after `create-invalidation` succeeds.

Verify roles with:

```powershell
aws iam get-role --role-name ROLE_NAME --output json
aws iam list-role-policies --role-name ROLE_NAME --output json
aws iam get-role-policy --role-name ROLE_NAME --policy-name POLICY_NAME --output json
aws iam list-attached-role-policies --role-name ROLE_NAME --output json
```

---

## 6. Standard Job Structure

Each repository should have two major job types:

```text
ci      Runs on pull requests only.
deploy  Runs on push/workflow_dispatch for main/prod only.
```

### 6.1 CI Job

CI should check the project without deploying.

Backend CI:

- Install Python dependencies.
- Run lint.
- Validate Supabase migration versions.
- Run tests.
- Build Docker image without pushing.

Frontend/marketing/help center CI:

- Install Node dependencies with `npm ci`.
- Run lint.
- Run typecheck if available.
- Run tests if available.
- Build production bundle.

### 6.2 Deploy Job

Deploy should:

1. Select staging values when `github.ref_name == 'main'`.
2. Select production values when `github.ref_name == 'prod'`.
3. Validate required GitHub Variables.
4. Configure AWS credentials through OIDC.
5. Build and publish the artifact.
6. Deploy to AWS.
7. Smoke test the public environment URL.

The deploy job should not:

- Read runtime application secrets from GitHub.
- Create or rewrite local `.env` files on servers.
- SSH into long-lived servers for normal deployments.
- Deploy from `develop`.

---

## 7. Backend API Pipeline Standard

Repository:

```text
velvet-elves-backend
```

Deployment target:

```text
main -> api.stage.velvetelves.com
prod -> api.velvetelves.com
```

Recommended AWS architecture:

- ECR for Docker images.
- ECS Fargate for the API service.
- ALB for public HTTP/HTTPS routing.
- ACM for TLS certificates.
- Route 53 for DNS.
- AWS Secrets Manager for runtime secrets.
- Supabase migrations run from GitHub Actions using a migration DB URL loaded from AWS Secrets Manager.

Required staging GitHub Variables:

```text
STAGE_AWS_DEPLOY_ROLE_ARN
STAGE_AWS_REGION
STAGE_ECR_REPOSITORY_URI
STAGE_ECS_CLUSTER
STAGE_ECS_SERVICE
STAGE_ECS_TASK_FAMILY
STAGE_ECS_DESIRED_COUNT
STAGE_BACKEND_SECRET_ID
STAGE_API_HEALTH_URL
```

Required production GitHub Variables:

```text
PROD_AWS_DEPLOY_ROLE_ARN
PROD_AWS_REGION
PROD_ECR_REPOSITORY_URI
PROD_ECS_CLUSTER
PROD_ECS_SERVICE
PROD_ECS_TASK_FAMILY
PROD_ECS_DESIRED_COUNT
PROD_BACKEND_SECRET_ID
PROD_API_HEALTH_URL
```

Backend image tags:

```text
main push -> main-<commit-sha>, stage-latest
prod push -> prod-<commit-sha>, prod-latest
```

Backend runtime secret locations:

```text
/velvet-elves/stage/backend
/velvet-elves/prod/backend
```

Backend smoke tests:

```text
https://api.stage.velvetelves.com/api/health
https://api.velvetelves.com/api/health
```

Backend rule:

Runtime values must be injected into ECS from AWS Secrets Manager and task-definition environment configuration. They must not be copied from GitHub into `.env` files during deployment.

---

## 8. Main Frontend Pipeline Standard

Repository:

```text
velvet-elves-frontend
```

Deployment target:

```text
main -> app.stage.velvetelves.com
prod -> app.velvetelves.com
```

Recommended AWS architecture:

- S3 private bucket for static assets.
- CloudFront distribution for public delivery.
- ACM certificate in `us-east-1` for CloudFront aliases.
- Route 53 alias record to CloudFront.

Required staging GitHub Variables:

```text
STAGE_AWS_DEPLOY_ROLE_ARN
STAGE_AWS_REGION
STAGE_FRONTEND_S3_BUCKET
STAGE_FRONTEND_CLOUDFRONT_ID
STAGE_FRONTEND_SITE_ORIGIN
STAGE_VITE_API_BASE_URL
STAGE_VITE_SUPABASE_URL
STAGE_VITE_SUPABASE_ANON_KEY
```

Required production GitHub Variables:

```text
PROD_AWS_DEPLOY_ROLE_ARN
PROD_AWS_REGION
PROD_FRONTEND_S3_BUCKET
PROD_FRONTEND_CLOUDFRONT_ID
PROD_FRONTEND_SITE_ORIGIN
PROD_VITE_API_BASE_URL
PROD_VITE_SUPABASE_URL
PROD_VITE_SUPABASE_ANON_KEY
```

Expected public API base URLs:

```text
STAGE_VITE_API_BASE_URL=https://api.stage.velvetelves.com
PROD_VITE_API_BASE_URL=https://api.velvetelves.com
```

Static deploy rules:

- Upload hashed assets with long immutable cache headers.
- Upload HTML with no-cache headers.
- Delete old source maps unless intentionally published.
- Invalidate CloudFront after upload.
- Smoke test the public URL after invalidation.

Smoke tests:

```text
https://app.stage.velvetelves.com
https://app.velvetelves.com
```

Frontend rule:

Never use backend service-role keys, private API keys, OAuth client secrets, or database URLs in frontend build variables.

---

## 9. Marketing Website Pipeline Standard

Repository:

```text
velvet-elves-marketing-website
```

Deployment target:

```text
main -> stage.velvetelves.com
prod -> velvetelves.com
```

Recommended AWS architecture:

- S3 private bucket for static assets.
- CloudFront distribution.
- Route 53 alias records.
- ACM certificate in `us-east-1` for CloudFront aliases.

Required staging GitHub Variables:

```text
STAGE_AWS_DEPLOY_ROLE_ARN
STAGE_AWS_REGION
STAGE_MARKETING_S3_BUCKET
STAGE_MARKETING_CLOUDFRONT_ID
STAGE_MARKETING_SITE_ORIGIN
STAGE_VITE_API_BASE_URL
```

Required production GitHub Variables:

```text
PROD_AWS_DEPLOY_ROLE_ARN
PROD_AWS_REGION
PROD_MARKETING_S3_BUCKET
PROD_MARKETING_CLOUDFRONT_ID
PROD_MARKETING_SITE_ORIGIN
PROD_VITE_API_BASE_URL
```

Expected public URLs:

```text
STAGE_MARKETING_SITE_ORIGIN=https://stage.velvetelves.com
PROD_MARKETING_SITE_ORIGIN=https://velvetelves.com
```

Marketing deploy rules:

- Build static site from the selected branch.
- Include SEO/prerender step if the repository supports it.
- Upload immutable assets with long cache headers.
- Upload HTML, sitemap, robots, and metadata files with no-cache headers.
- Invalidate CloudFront.
- Smoke test public homepage and key pages.

Smoke tests:

```text
https://stage.velvetelves.com
https://velvetelves.com
```

---

## 10. Help Center Pipeline Standard

Repository:

```text
velvet-elves-help-center
```

Deployment target:

```text
main -> help.stage.velvetelves.com
prod -> help.velvetelves.com
```

Recommended AWS architecture:

- S3 private bucket for static assets.
- CloudFront distribution.
- Route 53 alias records.
- ACM certificate in `us-east-1` for CloudFront aliases.

Required staging GitHub Variables:

```text
STAGE_AWS_DEPLOY_ROLE_ARN
STAGE_AWS_REGION
STAGE_HELP_S3_BUCKET
STAGE_HELP_CLOUDFRONT_ID
STAGE_HELP_SITE_ORIGIN
STAGE_VITE_HELP_API_BASE_URL
```

Required production GitHub Variables:

```text
PROD_AWS_DEPLOY_ROLE_ARN
PROD_AWS_REGION
PROD_HELP_S3_BUCKET
PROD_HELP_CLOUDFRONT_ID
PROD_HELP_SITE_ORIGIN
PROD_VITE_HELP_API_BASE_URL
```

Expected public values:

```text
STAGE_HELP_SITE_ORIGIN=https://help.stage.velvetelves.com
PROD_HELP_SITE_ORIGIN=https://help.velvetelves.com
STAGE_VITE_HELP_API_BASE_URL=https://api.stage.velvetelves.com
PROD_VITE_HELP_API_BASE_URL=https://api.velvetelves.com
```

Help center deploy rules:

- Build and prerender if supported.
- Upload immutable assets with long cache headers.
- Upload HTML and sitemap with no-cache headers.
- Invalidate CloudFront.
- Smoke test public help center URL.

Smoke tests:

```text
https://help.stage.velvetelves.com
https://help.velvetelves.com
```

---

## 11. Static Site Upload Standard

Use this upload behavior for frontend, marketing, and help center repositories.

Immutable assets:

```bash
aws s3 sync dist "s3://${SITE_S3_BUCKET}" \
  --exclude "*.html" \
  --exclude "sitemap.xml" \
  --exclude "robots.txt" \
  --exclude "*.map" \
  --cache-control "public,max-age=31536000,immutable" \
  --region "${AWS_REGION}"
```

HTML and metadata:

```bash
aws s3 sync dist "s3://${SITE_S3_BUCKET}" \
  --delete \
  --exclude "*" \
  --include "*.html" \
  --cache-control "no-cache,no-store,must-revalidate" \
  --content-type "text/html" \
  --region "${AWS_REGION}"
```

CloudFront invalidation:

```bash
invalidation_id=$(aws cloudfront create-invalidation \
  --distribution-id "${SITE_CLOUDFRONT_ID}" \
  --paths "/*" \
  --query "Invalidation.Id" \
  --output text)

aws cloudfront wait invalidation-completed \
  --distribution-id "${SITE_CLOUDFRONT_ID}" \
  --id "${invalidation_id}"
```

Do not upload source maps to public buckets unless intentionally needed for debugging and approved for the environment.

---

## 12. Validation Requirements

Each deployment workflow must validate all required GitHub Variables before doing work.

Example:

```bash
required=(
  AWS_DEPLOY_ROLE_ARN
  AWS_REGION
  SITE_S3_BUCKET
  SITE_CLOUDFRONT_ID
  SITE_ORIGIN
)

for name in "${required[@]}"; do
  if [ -z "${!name}" ]; then
    echo "::error::Missing required GitHub variable for ${DEPLOY_ENV}: ${name}"
    exit 1
  fi
done
```

Validation error messages must say `GitHub variable`, not `secret`, unless a real GitHub Secret is deliberately required.

---

## 13. Smoke Test Requirements

Every deploy must finish with a smoke test.

Backend:

```bash
curl --fail --silent --show-error "${API_HEALTH_URL}"
```

Static sites:

```bash
curl --fail --silent --show-error --location "${SITE_ORIGIN}" > /dev/null
```

Recommended additional checks:

- Confirm HTTPS works.
- Confirm expected domain is used after redirects.
- Confirm primary assets load.
- Confirm frontend can reach the correct API base URL.
- For static sites, test both `/` and a representative deep link.
- For CloudFront-backed SPAs, confirm `403` and `404` custom error responses return `/index.html` with response code `200`.
- If the custom domain returns `403`, check S3 objects before changing DNS. An empty private bucket commonly appears as `403` through CloudFront.
- If `curl` fails only from a restricted local shell, retry from the same shell context used for AWS CLI verification before concluding DNS is broken.

---

## 14. Rollback Strategy

Preferred rollback order:

1. Revert the bad commit or merge manually.
2. Push the corrected branch to trigger the pipeline.
3. If immediate rollback is required:
   - Backend: redeploy the previous ECS task definition revision or previous ECR image tag.
   - Static sites: redeploy the previous known-good branch commit or restore from S3/CloudFront artifact history if available.

The CI/CD pipeline should not auto-rollback production unless the behavior is deliberately designed and tested.

---

## 15. Required AWS Resources Per Repository

Backend API:

```text
ECR repository
ECS cluster
ECS service
ECS task definition family
ALB
Target group
ACM certificate
Route 53 record
AWS Secrets Manager runtime secret
GitHub OIDC deploy role
```

Static sites:

```text
S3 private hosting bucket
CloudFront distribution
ACM certificate in us-east-1
Route 53 alias record
GitHub OIDC deploy role
```

Environment separation:

- Staging and production should have separate S3 buckets.
- Staging and production should have separate CloudFront distributions.
- Staging and production backend services should use separate ECS services.
- Staging and production backend runtime secrets should be separate.
- Staging and production deploy roles should be separate where practical.

### 15.1 Static Site AWS Setup With AWS CLI

Use this sequence for frontend, marketing, and help center static-site
repositories.

Before starting:

```powershell
aws sts get-caller-identity --output json
aws configure get region
```

Confirm:

```text
Account: 388482955098
Region:  us-east-2 for S3 resources
Region:  us-east-1 for ACM certificates used by CloudFront
```

Create or verify the private S3 bucket:

```powershell
aws s3api create-bucket `
  --bucket SITE_BUCKET `
  --region us-east-2 `
  --create-bucket-configuration LocationConstraint=us-east-2

aws s3api put-public-access-block `
  --bucket SITE_BUCKET `
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

aws s3api get-public-access-block --bucket SITE_BUCKET --output json
```

Create or verify the CloudFront distribution:

- Use an S3 REST origin, not an S3 website endpoint.
- Use Origin Access Control (OAC), not public bucket access.
- Set `DefaultRootObject` to `index.html`.
- Add custom error responses for SPA routing:
  - `403 -> /index.html` with response code `200`
  - `404 -> /index.html` with response code `200`
- Use the CloudFront default certificate only for temporary domainless testing.
- Use an ACM certificate in `us-east-1` before attaching custom aliases.

Verify a distribution:

```powershell
aws cloudfront get-distribution `
  --id DISTRIBUTION_ID `
  --query "Distribution.{Status:Status,DomainName:DomainName,Aliases:DistributionConfig.Aliases.Items,DefaultRootObject:DistributionConfig.DefaultRootObject,Origins:DistributionConfig.Origins.Items[*].{Id:Id,DomainName:DomainName,OriginAccessControlId:OriginAccessControlId},Enabled:DistributionConfig.Enabled}" `
  --output json
```

Verify SPA fallback and certificate settings:

```powershell
aws cloudfront get-distribution-config `
  --id DISTRIBUTION_ID `
  --query "DistributionConfig.{Aliases:Aliases,ViewerCertificate:ViewerCertificate,DefaultRootObject:DefaultRootObject,CustomErrorResponses:CustomErrorResponses}" `
  --output json
```

CloudFront updates must use the full current distribution config and the
current `ETag`. Do not attempt to send only the fields you want to change.

Safe update pattern:

```powershell
$raw = aws cloudfront get-distribution-config --id DISTRIBUTION_ID | ConvertFrom-Json
$cfg = $raw.DistributionConfig

# Modify $cfg in memory, then write it to a temporary JSON file.
$cfg | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath cloudfront-config.json -Encoding ascii

aws cloudfront update-distribution `
  --id DISTRIBUTION_ID `
  --if-match $raw.ETag `
  --distribution-config file://cloudfront-config.json

aws cloudfront wait distribution-deployed --id DISTRIBUTION_ID
```

Attach or verify the bucket policy that lets only the intended CloudFront
distribution read objects:

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
      "Resource": "arn:aws:s3:::SITE_BUCKET/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::388482955098:distribution/DISTRIBUTION_ID"
        }
      }
    }
  ]
}
```

Verify:

```powershell
aws s3api get-bucket-policy --bucket SITE_BUCKET --query Policy --output text
aws s3api list-objects-v2 --bucket SITE_BUCKET --max-items 20 --output json
```

An empty bucket behind a private CloudFront distribution returns `403` until
the first deployment uploads `index.html` and assets. Treat that as an artifact
state, not necessarily a domain or policy failure.

### 15.2 Custom Domain Setup With ACM, CloudFront, And Route 53

CloudFront custom aliases require an issued ACM certificate in `us-east-1`.
Certificates in `us-east-2` cannot be used for CloudFront aliases.

Request the certificate:

```powershell
aws acm request-certificate `
  --region us-east-1 `
  --domain-name STAGE_SITE_DOMAIN `
  --subject-alternative-names PROD_SITE_DOMAIN `
  --validation-method DNS `
  --idempotency-token PROJECTSTATICYYYYMMDD `
  --query CertificateArn `
  --output text
```

Fetch DNS validation records:

```powershell
aws acm describe-certificate `
  --region us-east-1 `
  --certificate-arn CERTIFICATE_ARN `
  --query "Certificate.DomainValidationOptions[*].ResourceRecord" `
  --output json
```

Upsert the returned validation CNAMEs into the public Route 53 hosted zone:

```powershell
aws route53 list-hosted-zones-by-name `
  --dns-name velvetelves.com `
  --query "HostedZones[*].{Id:Id,Name:Name,PrivateZone:Config.PrivateZone}" `
  --output json
```

After submitting the Route 53 validation change:

```powershell
aws route53 wait resource-record-sets-changed --id CHANGE_ID

aws acm describe-certificate `
  --region us-east-1 `
  --certificate-arn CERTIFICATE_ARN `
  --query "Certificate.{Status:Status,DomainName:DomainName,SubjectAlternativeNames:SubjectAlternativeNames,ValidationStatuses:DomainValidationOptions[*].{Domain:DomainName,Status:ValidationStatus}}" `
  --output json
```

Do not attach the certificate to CloudFront until ACM status is `ISSUED`.

Attach the certificate and one alias to each environment distribution:

```text
staging distribution    alias STAGE_SITE_DOMAIN
production distribution alias PROD_SITE_DOMAIN
```

Use these CloudFront viewer certificate settings:

```text
ACMCertificateArn=CERTIFICATE_ARN
SSLSupportMethod=sni-only
MinimumProtocolVersion=TLSv1.2_2021
CertificateSource=acm
```

Use the safe CloudFront update pattern from section 15.1 when attaching
aliases, changing certificates, changing default root objects, or adding SPA
custom error responses.

Wait for CloudFront:

```powershell
aws cloudfront wait distribution-deployed --id DISTRIBUTION_ID
```

Create Route 53 `A` and `AAAA` alias records for each custom domain. CloudFront
hosted zone ID is global:

```text
Z2FDTNDATAQYW2
```

Alias target format:

```text
Name:                 help.stage.velvetelves.com.
Type:                 A and AAAA
Alias HostedZoneId:   Z2FDTNDATAQYW2
Alias DNSName:        dxxxxxxxxxxxxx.cloudfront.net.
EvaluateTargetHealth: false
```

Wait for Route 53:

```powershell
aws route53 wait resource-record-sets-changed --id CHANGE_ID
```

Verify:

```powershell
Resolve-DnsName STAGE_SITE_DOMAIN -Type A
Resolve-DnsName PROD_SITE_DOMAIN -Type A

curl.exe -I -L https://STAGE_SITE_DOMAIN
curl.exe -I -L https://PROD_SITE_DOMAIN
```

If staging returns `200` but production returns `403`, check whether production
S3 has deployed objects before changing DNS or CloudFront:

```powershell
aws s3api list-objects-v2 --bucket PROD_SITE_BUCKET --max-items 20 --output json
```

### 15.3 GitHub Variable Setup And Verification

Set GitHub repository Variables only after AWS resource names, IDs, and public
origins are known.

Temporary domainless static-site deployments may use CloudFront URLs:

```text
STAGE_SITE_ORIGIN=https://dxxxxxxxxxxxxx.cloudfront.net
PROD_SITE_ORIGIN=https://dyyyyyyyyyyyyy.cloudfront.net
```

After custom domains are attached and verified, update the same Variables:

```text
STAGE_SITE_ORIGIN=https://stage-or-subdomain.velvetelves.com
PROD_SITE_ORIGIN=https://production-or-subdomain.velvetelves.com
```

Do not leave GitHub Variables pointing at CloudFront default domains after
custom domains are live, because smoke tests should validate the real public
URL.

Verify repository Variables through the GitHub UI or API:

```text
Settings -> Secrets and variables -> Actions -> Variables
```

If migrating from an older workflow, delete obsolete GitHub Secrets with the
same purpose as the new Variables. For example, after moving a static-site
origin to `vars.STAGE_HELP_SITE_ORIGIN`, remove any stale
`secrets.STAGE_HELP_SITE_ORIGIN` unless a documented exception requires it.

---

## 16. Implementation Checklist For A New Repository

Before enabling deployment:

- Run AWS CLI preflight from the exact shell that will configure AWS.
- Confirm AWS caller identity is account `388482955098`.
- Confirm default or selected AWS region is correct.
- Confirm branches exist: `develop`, `main`, `prod`.
- Create or verify staging AWS resources.
- Create or verify production AWS resources.
- For static sites, confirm private S3 buckets exist and public access is blocked.
- For static sites, confirm CloudFront distributions use OAC and the correct S3 REST origins.
- For static sites, confirm CloudFront `DefaultRootObject=index.html`.
- For static SPAs, confirm CloudFront `403` and `404` custom errors route to `/index.html`.
- For custom domains, request or verify an ACM certificate in `us-east-1`.
- For custom domains, add or verify ACM DNS validation records in Route 53.
- For custom domains, wait until ACM certificate status is `ISSUED`.
- For custom domains, attach aliases and ACM certificate to CloudFront.
- For custom domains, create or verify Route 53 `A` and `AAAA` aliases to CloudFront.
- For temporary domainless setup, use CloudFront default URLs only until custom aliases are ready.
- Create GitHub OIDC deploy roles.
- Confirm OIDC trust is branch-scoped to `main` for staging and `prod` for production.
- Confirm deploy role permissions include required S3 actions.
- Confirm deploy role permissions include `cloudfront:CreateInvalidation` and `cloudfront:GetInvalidation`.
- Add GitHub Variables for staging.
- Add GitHub Variables for production.
- Update GitHub public origin Variables from CloudFront URLs to custom domains after DNS is live.
- Delete obsolete GitHub Secrets that were replaced by GitHub Variables.
- Confirm no runtime secrets are stored in GitHub.
- Add workflow with standard trigger pattern.
- Add CI job.
- Add deploy job.
- Add required variable validation.
- Add smoke test.
- Run local lint/build checks before opening the promotion PR.
- Run PR CI into `main`.
- Merge to `main` and confirm staging deploy.
- Confirm staging public URL returns `200`.
- Confirm staging frontend can call the expected public API base URL.
- Run PR CI into `prod`.
- Merge to `prod` and confirm production deploy.
- Confirm production public URL returns `200`.
- If production returns `403`, confirm whether the production bucket is empty before changing AWS domain settings.

---

## 17. Do Not Do These Things

- Do not deploy from `develop`.
- Do not store backend runtime secrets in GitHub Variables.
- Do not store backend runtime secrets in GitHub Secrets unless there is an explicit, documented exception.
- Do not use `vars.X || secrets.X` fallback.
- Do not include private keys or service-role keys in Vite builds.
- Do not use long-lived AWS access keys in GitHub.
- Do not SSH into servers for normal deployments if AWS-native deployment is available.
- Do not write production `.env` files from GitHub Actions.
- Do not point staging domains at production resources.
- Do not point production domains at staging resources.
- Do not assume AWS CLI is logged in for every shell just because one local terminal is logged in.
- Do not attach CloudFront aliases before the `us-east-1` ACM certificate is issued.
- Do not leave custom-domain GitHub Variables pointing at CloudFront default domains after DNS is live.
- Do not treat a CloudFront `403` as a domain failure until S3 bucket contents and bucket policy have been checked.
- Do not change `dev.velvetelves.com` as part of this CI/CD rollout.

---

## 18. Current Staging Backend Reference

Current known staging backend values:

```text
STAGE_AWS_DEPLOY_ROLE_ARN=arn:aws:iam::388482955098:role/velvet-elves-stage-backend-github-deploy
STAGE_AWS_REGION=us-east-2
STAGE_ECR_REPOSITORY_URI=388482955098.dkr.ecr.us-east-2.amazonaws.com/velvet-elves/backend
STAGE_ECS_CLUSTER=velvet-elves-stage
STAGE_ECS_SERVICE=velvet-elves-stage-backend
STAGE_ECS_TASK_FAMILY=velvet-elves-stage-backend
STAGE_ECS_DESIRED_COUNT=1
STAGE_BACKEND_SECRET_ID=/velvet-elves/stage/backend
STAGE_API_HEALTH_URL=https://api.stage.velvetelves.com/api/health
```

Current staging backend health URL:

```text
https://api.stage.velvetelves.com/api/health
```

Expected response:

```json
{"status":"ok","env":"staging","version":"0.1.0"}
```

---

## 19. Bottom Line

The CI/CD standard is:

```text
Manual Git promotion controls what deploys.
GitHub Variables describe where to deploy.
AWS Secrets Manager stores backend runtime secrets.
GitHub Actions builds, deploys, and smoke-tests.
develop never deploys.
main deploys staging.
prod deploys production.
```
