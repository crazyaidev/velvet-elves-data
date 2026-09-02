"""List staging deals for the logged-in QA user and hit email-plans by task name."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = os.environ.get("QA_API", "https://api.stage.velvetelves.com").rstrip("/")
EMAIL = os.environ.get("QA_EMAIL", "shyna.elene@minafter.com")
PASSWORD = os.environ.get("QA_PASSWORD", "QWE!@#asd234")
OUT = os.path.join(os.path.dirname(__file__), "artifacts_feature14_32_staging_deploy", "deals.json")


def req(method, path, token=None, data=None, form=None):
    url = f"{API}{path}"
    headers = {"Accept": "application/json"}
    body = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
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


def main():
    st, login = req("POST", "/api/v1/users/login", form={"username": EMAIL, "password": PASSWORD})
    print("login", st, (login or {}).get("user", {}).get("email") if isinstance(login, dict) else login)
    token = login["access_token"]
    st, me = req("GET", "/api/v1/users/me", token)
    print("me", json.dumps({k: me.get(k) for k in ("email", "role", "full_name", "tenant_id")}))
    st, listed = req("GET", "/api/v1/transactions?page=1&page_size=100", token)
    items = (listed or {}).get("items") or []
    print("tx count", (listed or {}).get("total"), "page", len(items))
    deals = []
    needles = (
        "Elm", "Birch", "Maple", "Pine", "Cedar", "Contract", "Dual", "Title",
        "Utility", "Warranty", "fix", "701", "202609",
    )
    for t in items:
        addr = t.get("address") or ""
        interesting = any(n.lower() in addr.lower() for n in needles)
        row = {
            "id": t.get("id"),
            "address": addr,
            "status": t.get("status"),
            "use_case": t.get("use_case"),
            "interesting": interesting,
        }
        if interesting or len(deals) < 15:
            stt, tasks = req("GET", f"/api/v1/tasks/transaction/{t['id']}?include_ai=true", token)
            names = []
            special = []
            if isinstance(tasks, list):
                names = [x.get("name") for x in tasks]
                for x in tasks:
                    if x.get("name") in {
                        "Appraisal Ordered", "Appraisal Completed", "Buyer Welcome",
                        "Order Title", "Loan Officer Welcome", "Confirm Title Order",
                        "Deliver Utility Info", "Deliver Title", "Inspection Response Reminder",
                    }:
                        special.append({
                            "id": x.get("id"),
                            "name": x.get("name"),
                            "target": x.get("target"),
                            "status": x.get("status"),
                            "automation_level": x.get("automation_level"),
                        })
            row["n_tasks"] = len(names) if isinstance(tasks, list) else None
            row["task_names"] = names
            row["special"] = special
            st_p, plan = req("GET", f"/api/v1/transactions/{t['id']}/plan", token)
            row["posture"] = ((plan or {}).get("automation") or {}).get("posture") if isinstance(plan, dict) else None
        deals.append(row)
        print(addr, t.get("use_case"), t.get("status"), row.get("posture"), "tasks", row.get("n_tasks"))

    with open(OUT, "w", encoding="utf8") as fh:
        json.dump({"email": EMAIL, "deals": deals}, fh, indent=2)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
