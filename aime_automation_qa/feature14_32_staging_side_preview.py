"""Confirm single-side Dual restore did not leak 305, and queue visibility."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

API = "https://api.stage.velvetelves.com"
EMAIL = "crazyaidev20500519@gmail.com"
PW = "QWE!@#asd234"
OUT = Path(__file__).resolve().parent / "artifacts_feature14_32_staging_deploy"


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
    with urllib.request.urlopen(r, timeout=60) as resp:
        raw = resp.read().decode()
        return resp.status, json.loads(raw) if raw else {}


def preview(token, use_case, representation_type, financing_type="Financed"):
    today = date.today()
    payload = {
        "address": "904 Side Probe Ave",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "use_case": use_case,
        "financing_type": financing_type,
        "representation_type": representation_type,
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
        "title_ordered_by": "us",
        "warranty_ordered_by": "us",
        "closing_mode": "title_escrow",
        "is_owner_occupied": True,
    }
    return req("POST", "/api/v1/transactions/preview-tasks", token, data=payload)


def summarize(body):
    titles = []
    utils = []
    appraisals = []
    combo = False
    for t in body.get("tasks") or []:
        name = t.get("name") or ""
        rec = {"name": name, "target": t.get("target")}
        if name == "Deliver Title":
            titles.append(rec)
            if t.get("target") == "Buyer & Seller":
                combo = True
        if name == "Deliver Utility Info":
            utils.append(rec)
        if "Appraisal" in name:
            appraisals.append(rec)
    return {"titles": titles, "utils": utils, "appraisals": appraisals, "combo305": combo, "n": len(body.get("tasks") or [])}


def main():
    _, login = req("POST", "/api/v1/users/login", form={"username": EMAIL, "password": PW})
    token = login["access_token"]
    out = {}
    for key, kwargs in (
        ("Buy-Fin", {"use_case": "Buy-Fin", "representation_type": "Buyer"}),
        ("Sell-Fin", {"use_case": "Sell-Fin", "representation_type": "Seller"}),
        ("Buy-Cash", {"use_case": "Buy-Cash", "representation_type": "Buyer", "financing_type": "Cash"}),
        ("Both-Fin", {"use_case": "Both-Fin", "representation_type": "Both"}),
    ):
        _, body = preview(token, **kwargs)
        out[key] = summarize(body)
        print(key, out[key])

    _, queue = req("GET", "/api/v1/tasks/queue", token)
    names = []
    maple = "9507baaf-ad8b-41ce-912c-6d637fbb9138"
    for g in (queue.get("groups") or []):
        for t in g.get("tasks") or []:
            if t.get("transaction_id") == maple:
                names.append(t.get("name"))
    out["queue_maple_names"] = names
    out["queue_maple_has_welcome"] = "Buyer Welcome" in names
    print("queue maple welcome", out["queue_maple_has_welcome"], "n", len(names))
    (OUT / "side_preview.json").write_text(json.dumps(out, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
