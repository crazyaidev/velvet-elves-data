"""Probe staging as platform admin for Jake/Audri file-logic QA."""
from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://api.stage.velvetelves.com"
EMAIL = "crazyaidev20500519@gmail.com"
PASSWORD = "QWE!@#qwe123"


def req(method: str, path: str, token: str | None = None, body: dict | None = None, timeout: int = 45):
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


def main():
    token = login()
    print("login ok")
    st, me = req("GET", "/api/v1/users/me", token)
    print("me", st, json.dumps({
        "id": me.get("id"),
        "email": me.get("email"),
        "role": me.get("role"),
        "is_platform_admin": me.get("is_platform_admin"),
        "is_tenant_owner": me.get("is_tenant_owner"),
        "tenant_id": me.get("tenant_id"),
        "full_name": me.get("full_name"),
        "onboarding_completed": me.get("onboarding_completed"),
    }))

    st, dash = req("GET", "/api/v1/dashboard/admin", token, timeout=60)
    print("admin dash", st, type(dash).__name__)
    if isinstance(dash, dict):
        print("by_status", dash.get("transactions_by_status"))
        print("pipeline", dash.get("pipeline_volume"))

    st, settings = req("GET", "/api/v1/automation/settings", token)
    print("automation settings", st, json.dumps(settings)[:1200] if settings else settings)

    st, status = req("GET", "/api/v1/automation/status", token, timeout=60)
    print("automation status", st)
    if isinstance(status, dict):
        keep = {k: status.get(k) for k in (
            "scheduler_healthy", "scheduler_state", "last_tick_at",
            "library_send_enabled", "scheduler_enabled", "tenant_last_run_at",
        ) if k in status}
        print("status bits", keep)
        print("status keys", list(status.keys())[:40])

    st, cards = req(
        "GET",
        "/api/v1/dashboard/transaction-cards?state_filter=all&page=1&page_size=50",
        token,
        timeout=60,
    )
    print("cards", st)
    items = []
    if isinstance(cards, dict):
        items = cards.get("items") or cards.get("cards") or []
        print("card keys", list(cards.keys())[:20], "n", len(items), "total", cards.get("total"))
    txs = []
    st, listed = req("GET", "/api/v1/transactions?page=1&page_size=100", token, timeout=60)
    print("tx list", st)
    if isinstance(listed, dict):
        txs = listed.get("items") or []
        print("tx total", listed.get("total"), "page n", len(txs))
    rows = []
    for t in txs:
        rows.append({
            "id": t.get("id"),
            "address": t.get("address") or t.get("property_address"),
            "status": t.get("status"),
            "use_case": t.get("use_case"),
            "has_appraisal": t.get("has_appraisal"),
        })
    print("tx rows", json.dumps(rows, indent=2)[:4000])

    cash = [t for t in txs if "Cash" in str(t.get("use_case") or "")]
    print("cash n", len(cash))
    for t in cash[:8]:
        tid = t["id"]
        st, tasks = req("GET", f"/api/v1/tasks/transaction/{tid}", token, timeout=45)
        names = []
        hits = []
        if isinstance(tasks, list):
            names = [x.get("name") for x in tasks]
            hits = [
                {
                    "id": x.get("id"),
                    "name": x.get("name"),
                    "legacy": (x.get("metadata_json") or {}).get("legacy_task_id"),
                    "target": x.get("target"),
                    "cc": x.get("cc_targets"),
                    "auto_draft": (x.get("metadata_json") or {}).get("auto_draft_email"),
                }
                for x in tasks
                if (x.get("metadata_json") or {}).get("legacy_task_id") in (265, 271, 420, 430, 260, 270)
                or "Appraisal" in str(x.get("name") or "")
                or "Closing Information" in str(x.get("name") or "")
            ]
        print("cash", t.get("use_case"), t.get("address"), "tasks", st, "hits", hits)

    closing_hits = []
    for t in txs[:40]:
        tid = t["id"]
        st, tasks = req("GET", f"/api/v1/tasks/transaction/{tid}", token, timeout=45)
        if not isinstance(tasks, list):
            continue
        for x in tasks:
            lid = (x.get("metadata_json") or {}).get("legacy_task_id")
            if lid in (420, 430, 265, 271) or "Closing Information" in str(x.get("name") or ""):
                closing_hits.append({
                    "tx": t.get("address"),
                    "use_case": t.get("use_case"),
                    "status": t.get("status"),
                    "name": x.get("name"),
                    "legacy": lid,
                    "target": x.get("target"),
                    "cc": x.get("cc_targets"),
                })
    print("special tasks", json.dumps(closing_hits, indent=2)[:5000])

    dump = {
        "me": {"email": me.get("email"), "role": me.get("role"), "tenant_id": me.get("tenant_id")},
        "automation_settings": settings,
        "tx_rows": rows,
        "closing_hits": closing_hits,
        "plans": [],
        "email_plans": [],
        "documents": [],
        "drafts": None,
        "needs_you": None,
        "templates_265_271_420_430": [],
        "appraisal_tasks": [],
    }

    st, drafts = req("GET", "/api/v1/ai-emails/drafts?limit=200", token, timeout=60)
    dump["drafts"] = {"status": st, "total": drafts.get("total") if isinstance(drafts, dict) else None}
    if isinstance(drafts, dict):
        items = drafts.get("items") or []
        slim = []
        for d in items[:40]:
            slim.append({
                "id": d.get("id") or d.get("log_id"),
                "subject": d.get("subject"),
                "transaction_id": d.get("transaction_id"),
                "approval_status": d.get("approval_status"),
                "attachment_ids": d.get("attachment_ids") or d.get("attachments"),
                "task_id": (d.get("metadata") or d.get("metadata_json") or {}).get("task_id")
                if isinstance(d.get("metadata") or d.get("metadata_json"), dict)
                else None,
            })
        dump["drafts"]["items"] = slim
        print("drafts", st, "n", drafts.get("total"), json.dumps(slim, indent=2)[:2500])

    st, ny = req("GET", "/api/v1/automation/needs-you", token, timeout=60)
    dump["needs_you"] = {"status": st}
    if isinstance(ny, dict):
        dump["needs_you"]["keys"] = list(ny.keys())[:30]
        dump["needs_you"]["total"] = ny.get("total") or ny.get("count")
        items = ny.get("items") or ny.get("tasks") or ny.get("blocked_tasks") or []
        dump["needs_you"]["n_items"] = len(items) if isinstance(items, list) else None
        print("needs-you", st, "keys", dump["needs_you"]["keys"], "n", dump["needs_you"]["n_items"])

    for q in ("Appraisal", "Closing Information", "265", "271"):
        st, tmpl = req(
            "GET",
            f"/api/v1/task-templates?search={q.replace(' ', '%20')}&page_size=50",
            token,
        )
        items = tmpl.get("items") if isinstance(tmpl, dict) else []
        for t in items or []:
            lid = t.get("legacy_task_id")
            if lid in (260, 265, 270, 271, 420, 430) or "Closing Information" in str(t.get("name") or "") or "Appraisal" in str(t.get("name") or ""):
                dump["templates_265_271_420_430"].append({
                    "legacy": lid,
                    "name": t.get("name"),
                    "target": t.get("target"),
                    "cc": t.get("cc_targets"),
                    "use_cases": t.get("use_cases"),
                    "automation_level": t.get("automation_level"),
                    "description": (t.get("description") or "")[:240],
                    "auto_draft": t.get("auto_draft_email"),
                })
    print("templates", json.dumps(dump["templates_265_271_420_430"], indent=2)[:4000])

    for t in txs:
        tid = t["id"]
        st, plan = req("GET", f"/api/v1/transactions/{tid}/plan", token, timeout=60)
        auto = plan.get("automation") if isinstance(plan, dict) else None
        dump["plans"].append({
            "id": tid,
            "address": t.get("address"),
            "plan_status": st,
            "automation": auto,
            "status": (plan or {}).get("status") if isinstance(plan, dict) else None,
        })
        st, docs = req("GET", f"/api/v1/documents/transaction/{tid}", token, timeout=45)
        doc_slim = []
        if isinstance(docs, list):
            for d in docs:
                doc_slim.append({
                    "id": d.get("id"),
                    "name": d.get("original_name") or d.get("file_name"),
                    "doc_type": d.get("doc_type"),
                    "status": d.get("status"),
                })
        dump["documents"].append({"tx": t.get("address"), "status": st, "n": len(doc_slim), "docs": doc_slim})

        st, tasks = req("GET", f"/api/v1/tasks/transaction/{tid}", token, timeout=45)
        if not isinstance(tasks, list):
            continue
        for x in tasks:
            name = str(x.get("name") or "")
            lid = (x.get("metadata_json") or {}).get("legacy_task_id")
            if (
                lid in (265, 271, 260, 270, 420, 430)
                or "Closing Information" in name
                or "Appraisal" in name
            ):
                dump["appraisal_tasks"].append({
                    "tx": t.get("address"),
                    "task_id": x.get("id"),
                    "name": name,
                    "status": x.get("status"),
                    "target": x.get("target"),
                    "cc": x.get("cc_targets"),
                    "legacy": lid,
                    "meta_keys": list((x.get("metadata_json") or {}).keys())[:20],
                    "ai_needs_user": (x.get("metadata_json") or {}).get("ai_needs_user"),
                    "auto_draft": (x.get("metadata_json") or {}).get("auto_draft_email"),
                    "playbook_key": (x.get("metadata_json") or {}).get("playbook_key"),
                })
                st_ep, eplan = req("GET", f"/api/v1/tasks/{x['id']}/email-plan", token, timeout=45)
                atts = []
                if isinstance(eplan, dict):
                    atts = eplan.get("attachments") or []
                    for leg in eplan.get("legs") or []:
                        atts = list(atts) + list(leg.get("attachments") or [])
                dump["email_plans"].append({
                    "tx": t.get("address"),
                    "task": name,
                    "status": st_ep,
                    "target_label": eplan.get("target_label") if isinstance(eplan, dict) else None,
                    "can_send": eplan.get("can_send") if isinstance(eplan, dict) else None,
                    "blocked": eplan.get("blocked_reason") if isinstance(eplan, dict) else None,
                    "to": [
                        {"email": r.get("email"), "role": r.get("role_label") or r.get("role")}
                        for r in ((eplan or {}).get("recipients") or [])
                    ] if isinstance(eplan, dict) else None,
                    "cc": [
                        {"email": c.get("email"), "role": c.get("role_label") or c.get("role")}
                        for c in ((eplan or {}).get("cc") or [])
                    ] if isinstance(eplan, dict) else None,
                    "attachments": atts,
                    "summary": (eplan.get("summary") if isinstance(eplan, dict) else None),
                })

    print("plans", json.dumps(dump["plans"], indent=2)[:3000])
    print("docs", json.dumps(dump["documents"], indent=2)[:3000])
    print("email_plans", json.dumps(dump["email_plans"], indent=2)[:6000])
    print("appraisal_tasks", json.dumps(dump["appraisal_tasks"], indent=2)[:4000])

    out_path = __file__.replace("_probe_staging.py", "artifacts_staging_2026-08-18")
    import os
    os.makedirs(out_path, exist_ok=True)
    with open(os.path.join(out_path, "api_probe.json"), "w", encoding="utf-8") as f:
        json.dump(dump, f, indent=2)
    print("wrote", os.path.join(out_path, "api_probe.json"))


if __name__ == "__main__":
    main()
