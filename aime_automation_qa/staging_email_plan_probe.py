"""Read-only email-plan checks on existing staging deals. Never sends."""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

API = os.environ.get("QA_API", "https://api.stage.velvetelves.com").rstrip("/")
EMAIL = os.environ.get("QA_EMAIL", "crazyaidev20500519@gmail.com")
PASSWORD = os.environ.get("QA_PASSWORD", "")

FIND = (
    "Order Title",
    "Confirm Title Order",
    "Order Home Warranty",
    "Buyer Closing Information",
    "Co-op Agent Welcome",
)


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
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"raw": raw[:1500]}
        return e.code, parsed


def main() -> int:
    if not PASSWORD:
        print("QA_PASSWORD required", file=sys.stderr)
        return 2
    status, login = req("POST", "/api/v1/users/login", form={"username": EMAIL, "password": PASSWORD})
    if status != 200:
        print("login fail", status, login)
        return 1
    token = login["access_token"]

    status, txs = req("GET", "/api/v1/transactions?page=1&page_size=40&sort_by=updated_at&sort_order=desc", token)
    items = (txs.get("items") if isinstance(txs, dict) else None) or []
    print(f"transactions={len(items)} status={status}")

    found: dict[str, dict] = {}
    for tx in items:
        tx_id = tx.get("id")
        addr = tx.get("address")
        st, tasks = req("GET", f"/api/v1/tasks/transaction/{tx_id}?include_ai=true", token)
        if st != 200 or not isinstance(tasks, list):
            continue
        for t in tasks:
            name = (t.get("name") or "").strip()
            if name in FIND and name not in found:
                found[name] = {"task": t, "tx": {"id": tx_id, "address": addr, "use_case": tx.get("use_case")}}
        if len(found) >= len(FIND):
            break

    fails = 0
    for name in FIND:
        hit = found.get(name)
        if not hit:
            print(f"[SKIP] plan.{name} — no open task on listed deals")
            continue
        task = hit["task"]
        tid = task["id"]
        st, plan = req("GET", f"/api/v1/tasks/{tid}/email-plan", token)
        atts = [a.get("filename") or a.get("name") or str(a) for a in (plan.get("attachments") or [])]
        att_blob = " ".join(atts).lower()
        body = (plan.get("body") or "")
        subject = plan.get("subject") or ""
        to_roles = [p.get("role") or p.get("label") or p.get("email") for p in (plan.get("recipients") or [])]
        print(f"\n=== {name} @ {hit['tx']['address']} ({hit['tx']['use_case']}) can_send={plan.get('can_send')} ===")
        print(f"to={to_roles} cc={[c.get('email') or c.get('label') for c in (plan.get('cc') or [])]}")
        print(f"subject={subject[:160]}")
        print(f"attachments={atts}")
        print(f"blocked={plan.get('blocked_reason')}")
        print(f"body_snip={body[:280].replace(chr(10), ' ')}")

        if name in ("Order Title", "Confirm Title Order"):
            bad = [a for a in atts if any(k in a.lower() for k in ("addend", "amendment", "closing disclosure", "closing_disclosure"))]
            ok_pkg = "withhold" if bad else "ok"
            result = "FAIL" if bad else "PASS"
            if result == "FAIL":
                fails += 1
            print(f"[{result}] {name}.no_addenda_or_cd — {ok_pkg} {bad}")
        if name == "Confirm Title Order":
            courtesy = "courtesy" in body.lower()
            result = "PASS" if courtesy else "FAIL"
            if result == "FAIL":
                fails += 1
            print(f"[{result}] Confirm Title Order.courtesy_script — courtesy={courtesy}")
        if name == "Order Home Warranty":
            to_agent = any("agent" in str(x).lower() or "account" in str(x).lower() for x in to_roles) or not to_roles
            warranty_co = "warranty" in " ".join(str(x).lower() for x in to_roles) and "home" in " ".join(str(x).lower() for x in to_roles)
            result = "FAIL" if warranty_co else "PASS"
            if result == "FAIL":
                fails += 1
            print(f"[{result}] Order Home Warranty.not_to_warranty_company — to={to_roles} target={task.get('target')}")
            print(f"[INFO] Order Home Warranty.draft_only_target={task.get('target')} auto={task.get('automation_level')}")
        if name == "Buyer Closing Information":
            cd = any("closing disclosure" in a.lower() or a.lower().endswith(" cd.pdf") or "closing_disclosure" in a.lower() for a in atts)
            result = "FAIL" if cd else "PASS"
            if result == "FAIL":
                fails += 1
            print(f"[{result}] Buyer Closing Information.no_cd_attachment — {atts}")
        if name == "Co-op Agent Welcome":
            print(f"[INFO] Co-op welcome cc={plan.get('cc')} body_has_signature={'sign' in body.lower()}")

    print(f"\nSUMMARY email-plan fails={fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
