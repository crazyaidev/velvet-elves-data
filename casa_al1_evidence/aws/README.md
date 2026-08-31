# CASA Fluid Attacks via CodeBuild

Linux Docker for SAST, driven from this Windows host with AWS CLI.

**Deleted 31 Aug 2026** (scans finished 21 Aug; XML/CSV already under `casa_al1_evidence/2026-08-21/`). Removed CodeBuild `velvet-elves-casa-fluid-sast`, IAM role `velvet-elves-casa-codebuild-role` (shared with ZAP), CloudWatch `/aws/codebuild/velvet-elves-casa-fluid-sast`, and `s3://velvet-elves-stage-codebuild-source-388482955098/casa-al1/`. Did **not** delete `velvet-elves-stage-backend-image-build` or the S3 bucket.

To recreate: `aws iam create-role` from `codebuild-trust.json`, `put-role-policy` from `codebuild-policy.json`, `aws codebuild create-project --cli-input-json file://codebuild-project.json --region us-east-2`.

`config.yaml` uses the current Fluid Attacks keys (`sast.include`). The 2022 ADA sample `path:` key is ignored by today’s CLI and produces an empty scan.

Do not put `.env` or `.venv` in the scan zip.

Re-pack: `python casa_al1_evidence/aws/pack_scan_zip.py` then `aws s3 cp` the zip to `casa-al1/velvet-elves-backend-scan.zip` and `aws codebuild start-build --project-name velvet-elves-casa-fluid-sast --region us-east-2`.
