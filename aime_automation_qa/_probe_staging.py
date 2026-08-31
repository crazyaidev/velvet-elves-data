"""Inventory staging as platform admin for Aime automation Chrome QA."""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = os.environ.get("QA_API", "https://api.stage.velvetelves.com")
EMAIL = os.environ.get("QA_EMAIL", "crazyaidev20500519@gmail.com")
PASSWORD = os.environ.get("QA_PASSWORD", "QWE!@#asd234")
OUT = os.path.join(os.path.dirname(__file__), "artifacts_staging_2026-08-19")
os.makedirs(OUT, exist_ok=True)


def req(method: str, path: str, token: str | None = None, body: dict | None = None, timeout: int = 60):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = Request(API + path, data=data, headers=headers, method=method)
    try:
        with urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else None
    except HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw) if raw else raw
        except Exception:
            parsed = raw
        return e.code, parsed


def login() -> str:
    data = urlencode({"username": EMAIL, "password": PASSWORD}).encode()
    r = Request(
        API + "/api/v1/users/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(r, timeout=30) as resp:
        body = json.loads(resp.read().decode())
    return body["access_token"]


def slim_tx(t: dict) -> dict:
    return {
        "id": t.get("id"),
        "address": t.get("address") or t.get("property_address"),
        "status": t.get("status"),
        "use_case": t.get("use_case"),
        "has_appraisal": t.get("has_appraisal"),
        "representation": t.get("representation_type") or t.get("representing"),
    }


def main():
    token = login()
    dump: dict = {"api": API, "email": EMAIL}

    st, me = req("GET", "/api/v1/users/me", token)
    dump["me"] = {
        "status": st,
        "id": (me or {}).get("id"),
        "email": (me or {}).get("email"),
        "role": (me or {}).get("role"),
        "full_name": (me or {}).get("full_name"),
        "is_platform_admin": (me or {}).get("is_platform_admin"),
        "is_tenant_owner": (me or {}).get("is_tenant_owner"),
        "tenant_id": (me or {}).get("tenant_id"),
        "onboarding_completed": (me or {}).get("onboarding_completed"),
    }
    print("me", json.dumps(dump["me"]))

    st, settings = req("GET", "/api/v1/automation/settings", token)
    dump["automation_settings"] = {"status": st, "body": settings}
    print("settings", st, json.dumps(settings)[:1500] if isinstance(settings, dict) else settings)

    st, status = req("GET", "/api/v1/automation/status", token)
    dump["automation_status"] = {"status": st}
    if isinstance(status, dict):
        dump["automation_status"]["body"] = {
            k: status.get(k)
            for k in (
                "scheduler_healthy",
                "scheduler_state",
                "last_tick_at",
                "library_send_enabled",
                "scheduler_enabled",
                "tenant_last_run_at",
                "mailbox_connected",
                "mailboxes_healthy",
                "mailboxes_connected",
                "last_tick_summary",
            )
            if k in status
        }
        dump["automation_status"]["keys"] = list(status.keys())
    print("status", json.dumps(dump["automation_status"])[:2000])

    st, listed = req("GET", "/api/v1/transactions?page=1&page_size=100", token)
    txs = (listed or {}).get("items") or [] if isinstance(listed, dict) else []
    dump["transactions"] = {
        "status": st,
        "total": (listed or {}).get("total") if isinstance(listed, dict) else None,
        "rows": [slim_tx(t) for t in txs],
    }
    print("tx total", dump["transactions"]["total"], "page", len(txs))

    st, ny = req("GET", "/api/v1/automation/needs-you", token)
    dump["needs_you"] = {"status": st}
    if isinstance(ny, dict):
        dump["needs_you"]["keys"] = list(ny.keys())
        dump["needs_you"]["total"] = ny.get("total") or ny.get("count")
        dump["needs_you"]["ready"] = ny.get("ready") or ny.get("ready_count")
        items = ny.get("items") or ny.get("tasks") or []
        dump["needs_you"]["n_items"] = len(items) if isinstance(items, list) else None
        sample = []
        for it in (items or [])[:12]:
            if not isinstance(it, dict):
                continue
            sample.append({
                "id": it.get("id"),
                "kind": it.get("kind") or it.get("bucket") or it.get("tile"),
                "title": it.get("title") or it.get("heading") or it.get("task_name"),
                "block": it.get("block_code") or it.get("reason_code"),
                "recovery_verb": it.get("recovery_verb"),
                "recovery_href": it.get("recovery_href"),
                "address": it.get("address") or it.get("deal_address"),
            })
        dump["needs_you"]["sample"] = sample
    print("needs-you", json.dumps(dump["needs_you"])[:2000])

    st, drafts = req("GET", "/api/v1/ai-emails/drafts?limit=50", token)
    dump["drafts"] = {"status": st}
    if isinstance(drafts, dict):
        dump["drafts"]["total"] = drafts.get("total")
        items = drafts.get("items") or []
        dump["drafts"]["sample"] = [
            {
                "id": d.get("id") or d.get("log_id"),
                "subject": d.get("subject"),
                "approval_status": d.get("approval_status"),
                "transaction_id": d.get("transaction_id"),
            }
            for d in items[:15]
        ]
    print("drafts", dump["drafts"].get("total"))

    deals = []
    for t in txs[:12]:
        tid = t["id"]
        st_p, plan = req("GET", f"/api/v1/transactions/{tid}/plan", token)
        auto = (plan or {}).get("automation") if isinstance(plan, dict) else None
        st_t, tasks = req("GET", f"/api/v1/tasks/transaction/{tid}", token)
        task_names = []
        special = []
        if isinstance(tasks, list):
            task_names = [x.get("name") for x in tasks[:40]]
            for x in tasks:
                name = str(x.get("name") or "")
                if any(
                    k in name
                    for k in (
                        "Welcome",
                        "Closing Information",
                        "Appraisal",
                        "Order Title",
                        "Inspection",
                    )
                ):
                    special.append({
                        "id": x.get("id"),
                        "name": name,
                        "status": x.get("status"),
                        "target": x.get("target"),
                    })
        st_d, docs = req("GET", f"/api/v1/documents/transaction/{tid}", token)
        doc_names = []
        if isinstance(docs, list):
            doc_names = [d.get("original_name") or d.get("file_name") for d in docs[:20]]
        st_c, parties = req("GET", f"/api/v1/transactions/{tid}/parties", token)
        party_slim = []
        if isinstance(parties, list):
            party_slim = [
                {
                    "role": p.get("party_role"),
                    "name": p.get("full_name") or p.get("company"),
                    "has_email": bool(p.get("email")),
                    "email_domain": (p.get("email") or "").split("@")[-1] if p.get("email") else None,
                }
                for p in parties
            ]
        deals.append({
            "id": tid,
            "address": t.get("address"),
            "status": t.get("status"),
            "use_case": t.get("use_case"),
            "plan_status": st_p,
            "automation": auto,
            "task_status": st_t,
            "n_tasks": len(tasks) if isinstance(tasks, list) else None,
            "special_tasks": special,
            "docs": doc_names,
            "parties": party_slim,
        })
        print("deal", t.get("address"), t.get("status"), auto, "special", len(special))

    dump["deals"] = deals
    path = os.path.join(OUT, "api_probe.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dump, f, indent=2)
    print("wrote", path)


if __name__ == "__main__":
    main()
