"""ZAP scan hook: attach the staging Bearer token without printing it.

zap-api-scan.py loads this via --hook. SCAN_BEARER is injected by CodeBuild
and passed into the container. Do not echo the token.
"""
from __future__ import annotations

import os


def zap_started(zap, target):  # noqa: ARG001
    token = (os.environ.get("SCAN_BEARER") or "").strip()
    if not token:
        raise RuntimeError("SCAN_BEARER is empty")
    zap.replacer.add_rule(
        description="casa-bearer",
        enabled=True,
        matchtype="REQ_HEADER",
        matchregex=False,
        matchstring="Authorization",
        replacement="Bearer " + token,
    )
