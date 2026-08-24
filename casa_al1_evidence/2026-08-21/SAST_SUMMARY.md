# Backend SAST — 21 Aug 2026 (Fluid Attacks on AWS CodeBuild)

Tool: `fluidattacks/sast:latest` in privileged CodeBuild (`velvet-elves-casa-fluid-sast`, us-east-2). CASA `checks:` from ADA `fluid-config.yaml`, adapted to the current CLI (`sast.include`, not the 2022 `path:` key). Output **CSV only**.

Target: `velvet-elves-backend` source zip (no `.venv`, no `.env`). SPA was **not** scanned (ADA: Fluid Attacks is not listed for TypeScript).

## Current keep

Build id: `velvet-elves-casa-fluid-sast:5999aab9-ffb9-4653-840c-069d192e97c9`  
Artifact: `s3://velvet-elves-stage-codebuild-source-388482955098/casa-al1/results/5999aab9-ffb9-4653-840c-069d192e97c9/fluid-sast-results`  
Local CSV: `casa_al1_evidence/2026-08-21/sast/5999aab9/extracted/Fluid-Attacks-Results.csv`

**0 High / 0 Critical / 0 Medium.** 3 Low remaining.

F266 (Dockerfile as root, Medium, CWE-250) is **closed** on this scan: `useradd` + `USER appuser`.

## Earlier builds (do not submit)

| Build | Why discard |
| --- | --- |
| `83f9509e-…` | Invalid: old ADA `path:` key was ignored; scanner reported “no supported languages.” |
| `62fa7106-193a-4106-b3c5-18a3c19a35fa` | Valid first pass. 1 Medium (F266) + 3 Low. Superseded after the non-root USER fix. |

## Findings (current scan)

| Check | Severity | CWE | Where | Notes |
| --- | --- | --- | --- | --- |
| F052 Insecure encryption algorithm | Low | CWE-328 | `app/services/intake_intelligence.py` SHA-1 for a short proposal id | Not token/PII encryption (that is Fernet). Compensating control unless a lab maps it as fail. |
| F380 Supply Chain Attack - Docker | Low | CWE-494 | `FROM python:3.12-slim` unpinned digest | Pin `python:3.12-slim@sha256:…` if the lab requires it. Do not pin a guessed digest (breaks ECS builds). |
| F418 Insecure service configuration - Docker | Low | CWE-530 | `COPY --chown=appuser:appuser . .` | `.dockerignore` exists (`logs/` added). Narrow COPY if the lab requires it. |

CLI ran unauthenticated (no Fluid Attacks SaaS token). That is expected for the free CASA CLI. `tracing_opt_out: true`.

## Re-run

From this Windows box (AWS CLI, account `388482955098`):

1. `python casa_al1_evidence/aws/pack_scan_zip.py`
2. `aws s3 cp casa_al1_evidence/2026-08-21/sast/velvet-elves-backend-scan.zip s3://velvet-elves-stage-codebuild-source-388482955098/casa-al1/velvet-elves-backend-scan.zip --region us-east-2 --sse AES256`
3. `aws codebuild start-build --project-name velvet-elves-casa-fluid-sast --region us-east-2`
