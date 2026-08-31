"""Drop cron, inbound webhooks, and (for auth scans) destructive routes.

Unauthenticated ZAP must not POST /internal/schedules/tick (even though the
cron secret fails closed). Inbound Stripe / DocuSign / email webhooks are
signature-gated; scanning them only floods logs.

Authenticated scans also strip DELETE and drop mail-send / OAuth-disconnect /
tenant-deletion paths so a platform-admin session cannot fire real mail or
disconnect Google.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request

DROP_EXACT = {
    "/api/v1/internal/schedules/tick",
    "/api/v1/esign/webhooks/docusign",
    "/api/v1/webhooks/stripe",
    "/api/v1/integrations/email/webhook/{provider}",
}

AUTH_DROP_EXACT = {
    "/api/v1/users/register",
    "/api/v1/users/password-reset/request",
    "/api/v1/users/password-reset/confirm",
    "/api/v1/tenants/current/schedule-deletion",
    "/api/v1/integrations/email/send",
    "/api/v1/ai-emails/send-ready",
    "/api/v1/ai-emails/compose",
    "/api/v1/ai-emails/test-inbound",
    "/api/v1/ai-emails/escalations/run",
    "/api/v1/ai-emails/reminders/run",
    "/api/v1/ai-emails/{log_id}/approve",
    "/api/v1/ai-emails/{log_id}/edit-and-send",
    "/api/v1/documents/{document_id}/email",
    "/api/v1/invoices/{invoice_id}/send",
    "/api/v1/automation/needs-you/send",
    "/api/v1/vendor-communications/send",
    "/api/v1/communication-logs/{log_id}/resend",
    "/api/v1/invitations/{invitation_id}/resend",
    "/api/v1/platform/users/{user_id}/send-password-reset",
    "/api/v1/platform/users/{user_id}/email",
    "/api/v1/platform/tenants/{tenant_id}/legal-hold",
    "/api/v1/platform/billing/purchases/{purchase_id}/refund",
}

HTTP_OPS = ("get", "post", "put", "patch", "delete", "head", "options")


def _load(src: str) -> dict:
    with urllib.request.urlopen(src, timeout=60) as resp:
        return json.load(resp)


def _drop_paths(paths: dict, exact: set[str]) -> list[str]:
    dropped = [p for p in list(paths) if p in exact]
    for p in dropped:
        del paths[p]
    return dropped


def _strip_delete_ops(paths: dict) -> int:
    removed = 0
    empty: list[str] = []
    for path, ops in paths.items():
        if "delete" in ops:
            del ops["delete"]
            removed += 1
        if not any(k in ops for k in HTTP_OPS):
            empty.append(path)
    for path in empty:
        del paths[path]
    return removed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("dest")
    parser.add_argument("--auth", action="store_true")
    args = parser.parse_args()

    spec = _load(args.src)
    paths = spec.get("paths") or {}
    dropped = _drop_paths(paths, DROP_EXACT)
    deleted_ops = 0
    if args.auth:
        dropped.extend(_drop_paths(paths, AUTH_DROP_EXACT))
        deleted_ops = _strip_delete_ops(paths)
    spec["servers"] = [{"url": "https://api.stage.velvetelves.com"}]
    with open(args.dest, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    print("openapi_paths_kept", len(paths))
    print("openapi_paths_dropped", dropped)
    print("openapi_delete_ops_stripped", deleted_ops)


if __name__ == "__main__":
    main()
