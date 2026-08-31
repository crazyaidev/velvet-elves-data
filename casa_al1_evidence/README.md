# CASA AL1 evidence (private)

Do not commit scan dumps that contain session cookies, JWTs, or full OpenAPI from a live authenticated crawl.

Official ADA configs (downloaded 21 Aug 2026):

- https://appdefensealliance.dev/static/casa/tier-2/files/fluid-config.zip
- https://appdefensealliance.dev/static/casa/tier-2/files/fluid-Dockerfile.zip
- https://appdefensealliance.dev/static/casa/tier-2/files/zap-casa-config.zip
- https://appdefensealliance.dev/static/casa/tier-2/files/zap-casa-api-config.zip

ADA note: the pre-configured Fluid Attacks CLI is **not** listed as compatible with TypeScript/JavaScript. Backend (Python/API) is the Fluid Attacks target. The SPA is covered by ZAP **web** + the API by ZAP **API** against staging OpenAPI.

## This machine (21 Aug 2026)

- **ZAP 2.17.0 + Temurin 17** under `tools/` (gitignored). Unauthenticated staging `-quickurl`: `2026-08-21/DAST_SUMMARY.md`.
- **No local Docker / WSL** (Windows Server t3.medium cannot nest WSL2). Fluid Attacks SAST runs on **AWS CodeBuild** instead: `2026-08-21/SAST_SUMMARY.md` and `aws/README.md`.

## Re-run Fluid Attacks (CodeBuild)

Zip the backend (no `.venv` / `.env`), upload to `s3://velvet-elves-stage-codebuild-source-388482955098/casa-al1/velvet-elves-backend-scan.zip`, then:

```bash
aws codebuild start-build --project-name velvet-elves-casa-fluid-sast --region us-east-2
```

## When a Linux Docker host exists (optional ZAP wrapper)


From a Linux/macOS/WSL shell, with official configs copied next to a source checkout:

```bash
# Backend SAST (CSV only — ADA asks for CSV or XML, not both)
docker build -t casascan -f configs/official/fluid-Dockerfile/fluid-Dockerfile .
docker run --rm -v /path/to/velvet-elves-backend:/usr/scan/app \
  casascan m gitlab:fluidattacks/universe@trunk /skims scan /usr/scan/app/config.yaml
```

Current Fluid Attacks image (if the 2022 Nix Dockerfile fails):

```bash
docker run --rm -v /path/to/velvet-elves-backend:/src \
  fluidattacks/sast:latest sast scan /src
```

Staging DAST (unauthenticated first; do not point at Jake’s brokerage or `algoforth33`):

```bash
cd configs/official
docker run --rm -v "$(pwd)":/zap/wrk/:rw -t zaproxy/zap-stable zap-full-scan.py \
  -t https://app.stage.velvetelves.com -P 8080 \
  -c zap-casa-config/zap-casa-config.conf \
  -x /zap/wrk/zap-staging-web.xml

docker run --rm -v "$(pwd)":/zap/wrk/:rw -t zaproxy/zap-stable zap-api-scan.py \
  -t https://api.stage.velvetelves.com/api/openapi.json -f openapi -P 8080 \
  -c zap-casa-api-config/zap-casa-api-config.conf \
  -x /zap/wrk/zap-staging-api.xml
```

Staging Swagger is still public by design (`APP_ENV=staging`). The API scan will see it.
