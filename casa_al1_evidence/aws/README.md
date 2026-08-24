# CASA Fluid Attacks via CodeBuild

Linux Docker for SAST, driven from this Windows host with AWS CLI. Project: `velvet-elves-casa-fluid-sast` in `us-east-2`. Role: `velvet-elves-casa-codebuild-role`. Source/results prefix: `s3://velvet-elves-stage-codebuild-source-388482955098/casa-al1/`.

`config.yaml` uses the current Fluid Attacks keys (`sast.include`). The 2022 ADA sample `path:` key is ignored by today’s CLI and produces an empty scan.

Do not put `.env` or `.venv` in the scan zip.

Re-pack: `python casa_al1_evidence/aws/pack_scan_zip.py` then `aws s3 cp` the zip to `casa-al1/velvet-elves-backend-scan.zip` and `aws codebuild start-build --project-name velvet-elves-casa-fluid-sast --region us-east-2`.
