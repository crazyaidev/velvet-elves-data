"""Live staging probe after the Feature 14-32 deploy. Read-only except login."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

API = "https://api.stage.velvetelves.com"
PW = "QWE!@#asd234"
OUT = Path(__file__).resolve().parent / "artifacts_feature14_32_staging_deploy"
OUT.mkdir(parents=True, exist_ok=True)


def req(method, path, token=None, data=None, form=None):
    headers = {"Accept": "application/json"}
    body = None
    if token:
        headers["Authorization"] = "Bearer " + token
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(API + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"raw": raw[:2000]}
        return e.code, parsed


def fetch_templates(token, active):
    items = []
    page = 1
    flag = "true" if active else "false"
    while True:
        status, body = req(
            "GET",
            f"/api/v1/task-templates?is_active={flag}&page={page}&page_size=200",
            token,
        )
        if status != 200:
            print("templates fail", active, status, body)
            return items
        items.extend(body.get("items") or [])
        if page >= (body.get("pages") or 1):
            break
        page += 1
    return items


def by_legacy(items):
    out = {}
    for t in items:
        lid = t.get("legacy_task_id")
        if lid is not None:
            out[int(lid)] = t
    return out


def preview(token, **kwargs):
    today = date.today()
    payload = {
        "address": kwargs.pop("address", "902 Dual Probe Ave"),
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "use_case": kwargs.pop("use_case", "Both-Fin"),
        "financing_type": kwargs.pop("financing_type", "Financed"),
        "representation_type": kwargs.pop("representation_type", "Both"),
        "purchase_price": 425000,
        "earnest_money": 5000,
        "earnest_money_days": 3,
        "contract_acceptance_date": str(today),
        "closing_date": str(today + timedelta(days=30)),
        "has_inspection": True,
        "inspection_days": 10,
        "inspection_response_days": 3,
        "has_hoa": False,
        "has_home_warranty": True,
        "has_appraisal": True,
        "title_ordered_by": kwargs.pop("title_ordered_by", "us"),
        "warranty_ordered_by": "us",
        "closing_mode": "title_escrow",
        "is_owner_occupied": True,
    }
    payload.update(kwargs)
    return req("POST", "/api/v1/transactions/preview-tasks", token, data=payload)


def main():
    dump = {"logins": {}, "findings": []}

    tokens = {}
    for email in (
        "crazyaidev20500519@gmail.com",
        "keison.londyn@minafter.com",
        "shyna.elene@minafter.com",
        "binisha.sophi@minafter.com",
    ):
        status, body = req(
            "POST", "/api/v1/users/login", form={"username": email, "password": PW}
        )
        user = (body.get("user") or {}) if isinstance(body, dict) else {}
        row = {
            "status": status,
            "mfa": body.get("mfa_required") if isinstance(body, dict) else None,
            "role": user.get("role"),
            "platform_admin": user.get("is_platform_admin"),
            "message": str(body.get("message") or body.get("detail") or "")[:200]
            if isinstance(body, dict)
            else "",
        }
        dump["logins"][email] = row
        print("login", email, status, row["message"][:80], "role", row["role"])
        if status == 200 and body.get("access_token"):
            tokens[email] = body["access_token"]

    email = "crazyaidev20500519@gmail.com"
    token = tokens.get(email)
    if not token:
        print("NO TOKEN")
        (OUT / "probe_now.json").write_text(json.dumps(dump, indent=2), encoding="utf8")
        return 1

    status, me = req("GET", "/api/v1/users/me", token)
    dump["me"] = {
        "status": status,
        "email": me.get("email"),
        "role": me.get("role"),
        "tenant_id": me.get("tenant_id"),
        "is_platform_admin": me.get("is_platform_admin"),
        "is_active": me.get("is_active"),
    }
    print("me", dump["me"])

    active = by_legacy(fetch_templates(token, True))
    inactive = by_legacy(fetch_templates(token, False))
    dump["library"] = {}
    print("=== library ===")
    for lid in (300, 305, 310, 150, 160, 265, 267, 271, 275):
        t = active.get(lid) or inactive.get(lid) or {}
        row = {
            "active": lid in active,
            "dual": t.get("dual_agency_behavior"),
            "target": t.get("target"),
            "id": t.get("id"),
            "desc": (t.get("description") or "")[:240],
        }
        dump["library"][str(lid)] = row
        print(lid, row["active"], row["dual"], row["target"], row["desc"][:70])

    status, both = preview(token, use_case="Both-Fin", representation_type="Both")
    ids = []
    titles = []
    utils = []
    welcomes = []
    for t in both.get("tasks") or []:
        lid = t.get("legacy_task_id")
        if lid is not None:
            ids.append(int(lid))
        name = t.get("name") or ""
        rec = {"name": name, "target": t.get("target"), "legacy": lid}
        if "Deliver Title" in name:
            titles.append(rec)
        if "Deliver Utility" in name:
            utils.append(rec)
        if "Welcome" in name:
            welcomes.append(rec)
    focus = sorted(set(ids) & {10, 20, 30, 150, 160, 300, 305, 310})
    dump["preview"] = {
        "status": status,
        "n": len(both.get("tasks") or []),
        "focus": focus,
        "titles": titles,
        "utils": utils,
        "welcomes": welcomes,
    }
    print("=== preview Both-Fin", status, "n", dump["preview"]["n"], "focus", focus)
    print("titles", titles)
    print("utils", utils)
    print("welcomes", welcomes)

    status, listed = req("GET", "/api/v1/transactions?page=1&page_size=100", token)
    items = (listed or {}).get("items") or [] if isinstance(listed, dict) else []
    dump["tx"] = {
        "status": status,
        "total": listed.get("total") if isinstance(listed, dict) else None,
        "page": len(items),
        "sample": [
            {
                "id": t.get("id"),
                "address": t.get("address"),
                "use_case": t.get("use_case"),
                "status": t.get("status"),
            }
            for t in items[:40]
        ],
    }
    print("=== tx", dump["tx"]["status"], "total", dump["tx"]["total"])
    for t in dump["tx"]["sample"]:
        print(" ", t["address"], t["use_case"], t["status"])

    needles = ("Elm", "Maple", "Cedar", "Dual", "Contract", "Utility", "Confirm", "fix", "701")
    interesting = [
        t
        for t in items
        if any(n.lower() in (t.get("address") or "").lower() for n in needles)
    ]
    dump["interesting"] = []
    for t in interesting[:20]:
        stt, tasks = req(
            "GET", f"/api/v1/tasks/transaction/{t['id']}?include_ai=true", token
        )
        names = [x.get("name") for x in tasks] if isinstance(tasks, list) else []
        dump["interesting"].append(
            {
                "id": t.get("id"),
                "address": t.get("address"),
                "use_case": t.get("use_case"),
                "n_tasks": len(names) if isinstance(tasks, list) else stt,
                "deliver_title": [
                    {"id": x.get("id"), "target": x.get("target")}
                    for x in (tasks or [])
                    if isinstance(tasks, list) and x.get("name") == "Deliver Title"
                ],
                "utility": [
                    {"id": x.get("id"), "target": x.get("target")}
                    for x in (tasks or [])
                    if isinstance(tasks, list) and x.get("name") == "Deliver Utility Info"
                ],
                "welcome_visible": "Buyer Welcome" in names,
            }
        )
        print(" interesting", t.get("address"), "tasks", len(names) if isinstance(tasks, list) else stt)

    status, ny = req("GET", "/api/v1/automation/needs-you", token)
    items_ny = (ny or {}).get("items") or [] if isinstance(ny, dict) else []
    verbs = sorted({it.get("recovery_verb") for it in items_ny if it.get("recovery_verb")})
    dump["needs_you"] = {
        "status": status,
        "n": len(items_ny),
        "verbs": verbs[:20],
        "sample": [
            {
                "title": it.get("title"),
                "code": it.get("block_code"),
                "verb": it.get("recovery_verb"),
                "href": it.get("recovery_href"),
            }
            for it in items_ny[:8]
        ],
    }
    print("=== needs-you", status, "n", len(items_ny), "verbs", verbs[:12])

    (OUT / "probe_now.json").write_text(json.dumps(dump, indent=2), encoding="utf8")
    print("wrote", OUT / "probe_now.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
