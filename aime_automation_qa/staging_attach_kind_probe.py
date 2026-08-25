"""Dump same-family Agent-target pairs and Confirm Title attachment kinds."""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

API = os.environ.get("QA_API", "https://api.stage.velvetelves.com").rstrip("/")
EMAIL = os.environ.get("QA_EMAIL", "crazyaidev20500519@gmail.com")
PASSWORD = os.environ.get("QA_PASSWORD", "")


def req(method, path, token=None, form=None):
    url = f"{API}{path}"
    headers = {"Accept": "application/json"}
    body = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=60) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def main():
    login = req("POST", "/api/v1/users/login", form={"username": EMAIL, "password": PASSWORD})
    token = login["access_token"]
    items = []
    for active in ("true", "false"):
        page = 1
        while True:
            body = req("GET", f"/api/v1/task-templates?is_active={active}&page={page}&page_size=200", token)
            items.extend(body.get("items") or [])
            if page >= (body.get("pages") or 1):
                break
            page += 1
    from collections import defaultdict
    groups = defaultdict(list)
    for t in items:
        if not t.get("is_active"):
            continue
        key = ((t.get("task_family") or t.get("name") or "").lower(), t.get("target"))
        groups[key].append(t)
    print("=== families with 2+ active rows same target ===")
    for key, rows in sorted(groups.items()):
        if len(rows) < 2:
            continue
        print(key, [(r.get("legacy_task_id"), r.get("use_cases"), r.get("dual_agency_behavior")) for r in rows])

    txs = req("GET", "/api/v1/transactions?page=1&page_size=40", token).get("items") or []
    for tx in txs:
        if "Sycamore" in (tx.get("address") or ""):
            tx_id = tx["id"]
            print(f"\n=== docs on {tx.get('address')} {tx_id} ===")
            docs = req("GET", f"/api/v1/documents/transaction/{tx_id}", token)
            if isinstance(docs, dict):
                docs = docs.get("items") or docs.get("documents") or docs
            if isinstance(docs, list):
                for d in docs:
                    print(
                        d.get("id"),
                        d.get("file_name") or d.get("original_name"),
                        d.get("doc_type"),
                        d.get("doc_label"),
                    )
            else:
                print(type(docs), str(docs)[:400])
            tasks = req("GET", f"/api/v1/tasks/transaction/{tx_id}?include_ai=true", token)
            for t in tasks if isinstance(tasks, list) else []:
                if t.get("name") == "Confirm Title Order":
                    plan = req("GET", f"/api/v1/tasks/{t['id']}/email-plan", token)
                    print("\nconfirm plan attachments full:")
                    print(json.dumps(plan.get("attachments"), indent=2)[:4000])
                    print("can_send", plan.get("can_send"), "target", plan.get("target_label"))
            break

    print("\n=== search Order Home Warranty ===")
    tasks = req("GET", "/api/v1/tasks?search=Order%20Home%20Warranty&include_ai=true&page_size=20", token)
    if isinstance(tasks, list):
        print("count", len(tasks))
        for t in tasks[:8]:
            print(t.get("name"), t.get("status"), t.get("target"), t.get("id"))
            if t.get("name") == "Order Home Warranty":
                plan = req("GET", f"/api/v1/tasks/{t['id']}/email-plan", token)
                print("  to", [p.get("email") or p.get("label") or p.get("role") for p in (plan.get("recipients") or [])])
                print("  body", (plan.get("body") or "")[:240].replace("\n", " "))
                print("  can_send", plan.get("can_send"), "blocked", plan.get("blocked_reason"))
                break


if __name__ == "__main__":
    main()
