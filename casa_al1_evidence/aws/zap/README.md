# CASA ZAP DAST via CodeBuild

Official ADA wrapper (`zap-full-scan.py` / `zap-api-scan.py`) against **staging**, unauthenticated. This Windows host has no Docker; CodeBuild runs `ghcr.io/zaproxy/zaproxy:stable`.

**Deleted 31 Aug 2026** with the Fluid SAST project. Recreate from `codebuild-project.json` (and the shared IAM role in `../codebuild-*.json`) if TAC asks for a rescan.

- SPA: `https://app.stage.velvetelves.com` + `zap-casa-config.conf`
- API: live OpenAPI minus cron tick and inbound webhooks + `zap-casa-api-config.conf`

Do not authenticate as platform admin or `algoforth33@gmail.com`. XML only for the lab.
