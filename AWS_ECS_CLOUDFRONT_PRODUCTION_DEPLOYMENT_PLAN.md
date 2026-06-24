# Velvet Elves - AWS ECS and CloudFront Production Deployment Plan

Date: 2026-06-24

Status: Planning document only. No source code changes are required by this document.

Target outcome:

- Move the FastAPI backend from EC2-hosted Docker to Amazon ECS on Fargate.
- Move the Vite/React frontend from EC2-hosted nginx Docker to S3 plus CloudFront.
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

- Frontend: `velvet-elves-frontend`
  - Vite, React 18, TypeScript.
  - Production build command: `npm run build`.
  - Built output directory: `dist`.
  - `VITE_API_BASE_URL` is a build-time value and must be set before `npm run build`.
  - Current frontend Docker/nginx config has SPA fallback to `index.html`.
  - Current nginx config explicitly serves `.mjs` files as JavaScript because the PDF worker can fail if `.mjs` is served with the wrong MIME type. The S3/CloudFront deployment must verify `.mjs` metadata.

- Current public dev references in docs:
  - Current shared dev frontend/backend origin: `https://dev.velvetelves.com`.
  - Production domains are not confirmed in the repo. This plan uses placeholders:
    - `APP_DOMAIN`: frontend domain, for example `app.velvetelves.com` or `velvetelves.com`.
    - `API_DOMAIN`: backend domain, for example `api.velvetelves.com`.

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

Recommended resource names:

| Resource | Name |
| --- | --- |
| AWS region | `us-east-2` unless the current AWS account standard says otherwise |
| ECS cluster | `velvet-elves-prod` |
| ECS service | `velvet-elves-prod-backend` |
| ECR repository | `velvet-elves/backend` |
| ALB | `velvet-elves-prod-api-alb` |
| ALB target group | `velvet-elves-prod-api-tg` |
| Backend log group | `/ecs/velvet-elves/prod/backend` |
| Backend secret | `/velvet-elves/prod/backend` |
| Frontend S3 bucket | `velvet-elves-prod-frontend-<account-id>` |
| Frontend CloudFront OAC | `velvet-elves-prod-frontend-oac` |
| Textract S3 bucket | keep current production bucket name from `TEXTRACT_S3_BUCKET` |

Use two environments if possible:

- `staging`: ECS/CloudFront stack using staging Supabase and staging provider credentials.
- `production`: ECS/CloudFront stack using production Supabase and production provider credentials.

If only one Supabase project exists today, do not use production ECS as a test bed for destructive migration checks. Run backend and frontend smoke tests against staging first or against a cloned Supabase project.

---

## 3. Production Domain and Certificate Decisions

Make these decisions before provisioning.

| Decision | Recommendation |
| --- | --- |
| Frontend domain | `APP_DOMAIN`, for example `app.velvetelves.com` or apex `velvetelves.com` |
| API domain | `API_DOMAIN`, for example `api.velvetelves.com` |
| Backend certificate | ACM certificate in the same region as the ALB, likely `us-east-2` |
| CloudFront certificate | ACM certificate in `us-east-1` |
| DNS | Route 53 aliases if the domain is hosted in Route 53; otherwise create provider-side CNAME/ALIAS records |
| API TLS termination | ALB terminates HTTPS on port `443`, forwards HTTP to ECS target port `8000` |
| Frontend TLS termination | CloudFront terminates HTTPS |

Important CloudFront certificate rule: CloudFront viewer certificates from ACM must be requested or imported in `us-east-1`.

---

## 4. Local CLI Setup

All AWS commands should be run from an authenticated shell. Examples are PowerShell-friendly.

```powershell
$REGION = "us-east-2"
$CF_CERT_REGION = "us-east-1"
$APP_DOMAIN = "app.velvetelves.com"
$API_DOMAIN = "api.velvetelves.com"
$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text

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
  --group-name velvet-elves-prod-api-alb-sg `
  --description "Velvet Elves production API ALB" `
  --vpc-id $VPC_ID `
  --region $REGION `
  --query GroupId --output text

aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $REGION
aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $REGION
```

Create an ECS task security group:

```powershell
$ECS_SG = aws ec2 create-security-group `
  --group-name velvet-elves-prod-backend-task-sg `
  --description "Velvet Elves production backend ECS tasks" `
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
aws logs create-log-group --log-group-name /ecs/velvet-elves/prod/backend --region $REGION
aws logs put-retention-policy --log-group-name /ecs/velvet-elves/prod/backend --retention-in-days 30 --region $REGION
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
APP_ENV=production
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
  --name /velvet-elves/prod/backend `
  --description "Velvet Elves production backend runtime secrets" `
  --secret-string file://aws-deploy-work/backend-prod-secrets.json `
  --region $REGION `
  --query ARN --output text
```

`backend-prod-secrets.json` should be created locally from the current production `.env` and never committed.

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
  --secret-id /velvet-elves/prod/backend `
  --region $REGION `
  --query ARN --output text

aws secretsmanager put-secret-value `
  --secret-id $BACKEND_SECRET_ARN `
  --secret-string file://aws-deploy-work/backend-prod-secrets.json `
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
  --role-name velvet-elves-prod-ecs-execution-role `
  --assume-role-policy-document file://aws-deploy-work/ecs-task-trust-policy.json

aws iam attach-role-policy `
  --role-name velvet-elves-prod-ecs-execution-role `
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

aws iam create-role `
  --role-name velvet-elves-prod-backend-task-role `
  --assume-role-policy-document file://aws-deploy-work/ecs-task-trust-policy.json
```

Create and attach inline policies:

```powershell
aws iam put-role-policy `
  --role-name velvet-elves-prod-ecs-execution-role `
  --policy-name velvet-elves-prod-read-backend-secrets `
  --policy-document file://aws-deploy-work/ecs-execution-secrets-policy.json

aws iam put-role-policy `
  --role-name velvet-elves-prod-backend-task-role `
  --policy-name velvet-elves-prod-textract-s3-policy `
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
$IMAGE_URI = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/velvet-elves/backend:$IMAGE_TAG"

docker build -t velvet-elves-backend:$IMAGE_TAG .
docker tag velvet-elves-backend:$IMAGE_TAG $IMAGE_URI
docker push $IMAGE_URI
```

Also tag a deployment alias only after the image passes ECS smoke tests:

```powershell
docker tag velvet-elves-backend:$IMAGE_TAG "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/velvet-elves/backend:prod-latest"
docker push "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/velvet-elves/backend:prod-latest"
```

### 7.4 Create ALB Target Group and Listeners

Create target group:

```powershell
$TG_ARN = aws elbv2 create-target-group `
  --name velvet-elves-prod-api-tg `
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
  --name velvet-elves-prod-api-alb `
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
  "family": "velvet-elves-prod-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/velvet-elves-prod-ecs-execution-role",
  "taskRoleArn": "arn:aws:iam::<account-id>:role/velvet-elves-prod-backend-task-role",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account-id>.dkr.ecr.<region>.amazonaws.com/velvet-elves/backend:<image-tag>",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        { "name": "APP_ENV", "value": "production" },
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
          "awslogs-group": "/ecs/velvet-elves/prod/backend",
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
- Replace `<backend-secret-arn>` with the full ARN returned by `aws secretsmanager describe-secret --secret-id /velvet-elves/prod/backend --query ARN --output text`.

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
aws ecs create-cluster --cluster-name velvet-elves-prod --region $REGION
```

Create service:

```powershell
aws ecs create-service `
  --cluster velvet-elves-prod `
  --service-name velvet-elves-prod-backend `
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
  --cluster velvet-elves-prod `
  --services velvet-elves-prod-backend `
  --region $REGION
```

Check task health:

```powershell
aws ecs describe-services `
  --cluster velvet-elves-prod `
  --services velvet-elves-prod-backend `
  --region $REGION `
  --query "services[0].{Running:runningCount,Desired:desiredCount,Deployments:deployments[*].{Status:status,Rollout:rolloutState,TaskDef:taskDefinition}}"
```

### 7.7 Backend DNS

After the ALB is healthy, create `API_DOMAIN` DNS.

Route 53 alias example:

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
  "Comment": "Point API domain to production ALB",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.velvetelves.com",
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
$FRONTEND_BUCKET = "velvet-elves-prod-frontend-$ACCOUNT_ID"

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

Do not enable S3 static website hosting for the production frontend bucket. Use the S3 REST origin with CloudFront Origin Access Control so the bucket stays private.

### 8.2 Build Frontend for Production

```powershell
cd C:\Projects\velvet-elves-frontend

$env:VITE_API_BASE_URL = "https://$API_DOMAIN"
$env:VITE_APP_ENV = "production"
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
  "Name": "velvet-elves-prod-frontend-oac",
  "Description": "OAC for Velvet Elves production frontend S3 origin",
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
  "Name": "velvet-elves-prod-frontend-cache",
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
  --query "CachePolicyList.Items[?CachePolicy.CachePolicyConfig.Name=='velvet-elves-prod-frontend-cache'].CachePolicy.Id | [0]" `
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
  --name velvet-elves-prod-spa-rewrite `
  --function-config Comment="Velvet Elves SPA route rewrite",Runtime=cloudfront-js-2.0 `
  --function-code fileb://aws-deploy-work/spa-rewrite.js

$SPA_FUNCTION_ETAG = aws cloudfront describe-function `
  --name velvet-elves-prod-spa-rewrite `
  --stage DEVELOPMENT `
  --query ETag `
  --output text

aws cloudfront publish-function `
  --name velvet-elves-prod-spa-rewrite `
  --if-match $SPA_FUNCTION_ETAG

$SPA_FUNCTION_ARN = aws cloudfront describe-function `
  --name velvet-elves-prod-spa-rewrite `
  --stage LIVE `
  --query "FunctionSummary.FunctionMetadata.FunctionARN" `
  --output text
```

If the function already exists, update the DEVELOPMENT stage, publish it, and then use the LIVE ARN:

```powershell
$SPA_FUNCTION_ETAG = aws cloudfront describe-function `
  --name velvet-elves-prod-spa-rewrite `
  --stage DEVELOPMENT `
  --query ETag `
  --output text

aws cloudfront update-function `
  --name velvet-elves-prod-spa-rewrite `
  --if-match $SPA_FUNCTION_ETAG `
  --function-config Comment="Velvet Elves SPA route rewrite",Runtime=cloudfront-js-2.0 `
  --function-code fileb://aws-deploy-work/spa-rewrite.js

$SPA_FUNCTION_ETAG = aws cloudfront describe-function `
  --name velvet-elves-prod-spa-rewrite `
  --stage DEVELOPMENT `
  --query ETag `
  --output text

aws cloudfront publish-function `
  --name velvet-elves-prod-spa-rewrite `
  --if-match $SPA_FUNCTION_ETAG

$SPA_FUNCTION_ARN = aws cloudfront describe-function `
  --name velvet-elves-prod-spa-rewrite `
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
  "CallerReference": "velvet-elves-prod-frontend-20260624",
  "Aliases": {
    "Quantity": 1,
    "Items": ["app.velvetelves.com"]
  },
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "velvet-elves-prod-frontend-s3",
        "DomainName": "velvet-elves-prod-frontend-<account-id>.s3.us-east-2.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        },
        "OriginAccessControlId": "<oac-id>"
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "velvet-elves-prod-frontend-s3",
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
  "Comment": "Velvet Elves production frontend",
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
      "Resource": "arn:aws:s3:::velvet-elves-prod-frontend-<account-id>/*",
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

Route 53 alias example:

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
        "Name": "app.velvetelves.com",
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

## 9. Phase 4 - Production Callback and Webhook Mapping

When moving domains, callbacks and webhooks are the easiest place to lose production behavior. Use this checklist.

### 9.1 Backend Environment Values

Set these backend values for production ECS:

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

Update the production Supabase project:

- Site URL: `https://APP_DOMAIN`.
- Redirect URLs:
  - `https://APP_DOMAIN/auth/callback`
  - `https://APP_DOMAIN/login`
  - Any tenant/custom-domain URLs already supported by the app.

This is not an AWS CLI action, but it is mandatory for production auth links, password reset links, and invite flows.

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

Change production deploy from GHCR plus SSH plus Docker Compose to:

1. Build Docker image.
2. Login to ECR.
3. Push image to ECR with immutable tag `${GITHUB_SHA}` and alias tag `main-latest`.
4. Run Supabase migrations exactly as the current backend workflow does.
5. Ensure the Textract S3 bucket exists and has private/encrypted/lifecycle settings.
6. Render or patch ECS task definition with the new image URI.
7. Register new task definition revision.
8. `aws ecs update-service --cluster velvet-elves-prod --service velvet-elves-prod-backend --task-definition <new-task-def>`.
9. `aws ecs wait services-stable`.
10. Smoke test:
    - `https://API_DOMAIN/api/health`
    - `https://API_DOMAIN/api/v1/health/ready`

GitHub Actions should use AWS OIDC, not long-lived AWS access keys.

Keep the migration database URL as a deployment secret, not an ECS runtime environment variable. The existing workflow uses the secret name `SUPABASE_DB_URL`; if you introduce a clearer `SUPABASE_MIGRATION_DB_URL`, update the workflow and manual runbooks together so operators do not accidentally run migrations against the application's runtime pooler URL.

### 10.2 Backend Manual Deploy Command Sequence

Manual release sequence until CI/CD is updated:

```powershell
# 1. Build and push image
cd C:\Projects\velvet-elves-backend
$IMAGE_TAG = "$(git rev-parse --short HEAD)-$(Get-Date -Format yyyyMMddHHmmss)"
$IMAGE_URI = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/velvet-elves/backend:$IMAGE_TAG"
docker build -t velvet-elves-backend:$IMAGE_TAG .
docker tag velvet-elves-backend:$IMAGE_TAG $IMAGE_URI
docker push $IMAGE_URI

# 2. Apply Supabase migrations before shifting traffic.
# Stop here if migrations fail.
$env:SUPABASE_MIGRATION_DB_URL = "<production-supabase-migration-db-url>"
supabase db push --include-all --yes --db-url "$env:SUPABASE_MIGRATION_DB_URL"

# 3. Confirm the Textract S3 bucket is private, encrypted, and has cleanup lifecycle.
# Run the existing deploy/ensure-textract-s3.sh from Git Bash/WSL, or execute equivalent AWS CLI checks.

# 4. Update task definition JSON image field manually or via jq in a non-Windows shell.
# 5. Register task definition.
$TASK_DEF_ARN = aws ecs register-task-definition --cli-input-json file://aws-deploy-work/backend-task-definition.json --query "taskDefinition.taskDefinitionArn" --output text --region $REGION

# 6. Update service.
aws ecs update-service --cluster velvet-elves-prod --service velvet-elves-prod-backend --task-definition $TASK_DEF_ARN --region $REGION
aws ecs wait services-stable --cluster velvet-elves-prod --services velvet-elves-prod-backend --region $REGION

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

Change production deploy from GHCR plus SSH plus Docker Compose to:

1. Build with production Vite variables:
   - `VITE_API_BASE_URL=https://API_DOMAIN`
   - `VITE_APP_ENV=production`
   - `VITE_GOOGLE_MAPS_API_KEY=<restricted key if used>`
2. Sync `dist` to S3 with cache-control rules.
3. Ensure `.mjs` assets have JavaScript content type.
4. Invalidate `/` and `/index.html` in CloudFront.
5. Smoke test `https://APP_DOMAIN/` and one deep link.

### 10.4 Frontend Manual Deploy Command Sequence

```powershell
cd C:\Projects\velvet-elves-frontend

$env:VITE_API_BASE_URL = "https://$API_DOMAIN"
$env:VITE_APP_ENV = "production"
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

---

## 11. Phase 6 - Production Cutover Plan

### 11.1 Parallel Environment First

Before moving real users:

1. Deploy ECS backend behind the new ALB.
2. Deploy frontend to S3/CloudFront.
3. Use temporary validation hostnames if possible:
   - `api-next.velvetelves.com`
   - `app-next.velvetelves.com`
4. Set backend `CORS_ORIGINS` to include both old and new frontend hostnames during validation.
5. Build frontend with the new API hostname.
6. Verify end-to-end.

### 11.2 DNS TTL

At least 24 hours before cutover:

- Lower old frontend and API DNS TTLs to `300` seconds.
- Confirm Route 53 or external DNS changes are ready.

### 11.3 Cutover Steps

1. Announce maintenance window if needed.
2. Pause EC2 production deploy workflow.
3. Confirm no Supabase migration is currently running.
4. Deploy latest backend image to ECS.
5. Deploy latest frontend build to S3/CloudFront.
6. Update production backend secret/config:
   - `FRONTEND_URL=https://APP_DOMAIN`
   - `CORS_ORIGINS=https://APP_DOMAIN`
   - all production callback URLs using `API_DOMAIN`.
7. Apply the backend configuration update using the correct ECS mechanism:
   - If only Secrets Manager values changed, force a new deployment so the running tasks fetch the latest secret values.
   - If task-definition `environment` values, the image URI, log settings, or resource sizing changed, register a new task definition revision and update the service to that revision.

   Secret-only refresh:

   ```powershell
   aws ecs update-service `
     --cluster velvet-elves-prod `
     --service velvet-elves-prod-backend `
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
     --cluster velvet-elves-prod `
     --service velvet-elves-prod-backend `
     --task-definition $TASK_DEF_ARN `
     --region $REGION
   ```

8. Wait for service stability.
9. Update DNS:
   - `API_DOMAIN` -> ALB alias.
   - `APP_DOMAIN` -> CloudFront alias.
10. Update external providers if not already done:
   - Supabase Auth.
   - Google/Microsoft OAuth.
   - Google Pub/Sub push subscription.
   - Microsoft Graph subscriptions.
   - DocuSign OAuth and Connect.
   - Stripe webhook.
11. Smoke test from a clean browser session.
12. Monitor logs and alarms for at least 2 hours after cutover.

### 11.4 Keep EC2 as Warm Rollback

Keep current EC2 infrastructure available for at least 7 days after cutover.

- Do not terminate EC2 immediately.
- Do not delete old DNS records immediately.
- Disable automatic EC2 deploys once ECS is serving production.
- After confidence window, stop EC2 instances before terminating them.

---

## 12. Rollback Plan

### 12.1 Backend Rollback

Preferred rollback if ECS is healthy but latest image is bad:

```powershell
aws ecs update-service `
  --cluster velvet-elves-prod `
  --service velvet-elves-prod-backend `
  --task-definition <previous-working-task-definition-arn> `
  --region $REGION

aws ecs wait services-stable `
  --cluster velvet-elves-prod `
  --services velvet-elves-prod-backend `
  --region $REGION
```

Fallback rollback if ECS/ALB stack is bad:

- Point `API_DOMAIN` DNS back to the existing EC2 backend.
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

- Point `APP_DOMAIN` DNS back to the EC2 frontend.

Important:

- If the frontend was built with a different `VITE_API_BASE_URL`, the rollback artifact must match the API domain currently in use.

### 12.3 Provider Callback Rollback

If rolling back domains:

- Stripe can temporarily keep both old and new webhook endpoints active.
- DocuSign Connect may need old URL restored.
- Google/Microsoft OAuth redirect URLs can usually contain both old and new URLs.
- Gmail Pub/Sub and Microsoft Graph subscriptions may need old push endpoints restored or recreated.

---

## 13. Production Validation Checklist

Run these checks before and after DNS cutover.

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

Minimum production alarms:

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
aws ecs describe-services --cluster velvet-elves-prod --services velvet-elves-prod-backend --region $REGION
aws elbv2 describe-target-health --target-group-arn $TG_ARN --region $REGION
aws logs tail /ecs/velvet-elves/prod/backend --follow --region $REGION
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
  --resource-id service/velvet-elves-prod/velvet-elves-prod-backend `
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
  --resource-id service/velvet-elves-prod/velvet-elves-prod-backend `
  --scalable-dimension ecs:service:DesiredCount `
  --policy-name velvet-elves-prod-backend-cpu60 `
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

- Backend production traffic is served by ECS Fargate, not EC2.
- Frontend production traffic is served by CloudFront and private S3, not EC2.
- `APP_DOMAIN` loads the SPA and supports hard-refresh deep links.
- `API_DOMAIN` serves backend health and authenticated APIs.
- CORS is clean from the production frontend.
- Supabase Auth login, password reset, and invite flows use the production frontend domain.
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
