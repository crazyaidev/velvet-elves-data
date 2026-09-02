"""Create one synthetic Buy-Fin file for Jake local Chrome QA. No tokens printed."""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib import error, parse, request

API = "http://127.0.0.1:8000"
EMAIL = "shyna.elene@minafter.com"
PASSWORD = "QWE!@#asd234"
OUT = Path(r"c:\Projects\velvet-elves-data\aime_automation_qa\artifacts_jake_local")
OUT.mkdir(parents=True, exist_ok=True)


def post_form(path: str, data: dict) -> tuple[int, dict]:
    body = parse.urlencode(data).encode()
    req = request.Request(API + path, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"raw": raw[:800]}
        return exc.code, payload


def call(method: str, path: str, token: str, payload: dict | None = None) -> tuple[int, object]:
    data = None if payload is None else json.dumps(payload).encode()
    r = request.Request(API + path, data=data, method=method)
    r.add_header("Authorization", f"Bearer {token}")
    if payload is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with request.urlopen(r, timeout=60) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, json.loads(raw) if raw else None
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"raw": raw[:1200]}
        return exc.code, body


def main() -> int:
    st, body = post_form("/api/v1/users/login", {"username": EMAIL, "password": PASSWORD})
    if st != 200 or not isinstance(body, dict) or not body.get("access_token"):
        print("login_fail", st)
        return 1
    if body.get("mfa_required"):
        print("login_mfa_required")
        return 2
    token = body["access_token"]
    user = body.get("user") or {}
    print(
        "login_ok",
        json.dumps(
            {
                "role": user.get("role"),
                "platform_admin": user.get("is_platform_admin"),
            }
        ),
    )

    st, settings = call("GET", "/api/v1/automation/settings", token)
    skeys = sorted(settings.keys()) if isinstance(settings, dict) else []
    print(
        "settings",
        st,
        json.dumps(
            {
                "default_posture": settings.get("default_posture") if isinstance(settings, dict) else None,
                "obligation_autonomy": settings.get("obligation_autonomy") if isinstance(settings, dict) else None,
                "has_obligation_autonomies": "obligation_autonomies" in skeys,
                "keys": skeys,
            }
        ),
    )
    st_put, after = call(
        "PUT",
        "/api/v1/automation/settings",
        token,
        {"obligation_autonomy": "manual"},
    )
    print(
        "settings_reset_dates",
        st_put,
        after.get("obligation_autonomy") if isinstance(after, dict) else after,
    )

    st, exceptions = call("GET", "/api/v1/automation/exceptions", token)
    print("exceptions", st, type(exceptions).__name__, len(exceptions) if isinstance(exceptions, list) else exceptions)

    accept = date(2026, 8, 20)
    close = date(2026, 10, 15)
    payload = {
        "address": "881 Jake TME Local Test Ln",
        "city": "Carmel",
        "state": "IN",
        "zip_code": "46032",
        "use_case": "Buy-Fin",
        "financing_type": "Financed",
        "representation_type": "Buyer",
        "purchase_price": 425000,
        "contract_acceptance_date": accept.isoformat(),
        "closing_date": close.isoformat(),
        "inspection_days": 10,
        "inspection_response_days": 3,
        "has_inspection": True,
        "status": "Active",
        "notes": "Synthetic Jake TME local QA file. Safe to terminate. Do not send mail.",
    }
    st, tx = call("POST", "/api/v1/transactions", token, payload)
    if st not in (200, 201) or not isinstance(tx, dict) or not tx.get("id"):
        print("create_fail", st, json.dumps(tx, default=str)[:1200])
        return 3
    tx_id = tx["id"]
    print("created", tx_id, tx.get("status"), tx.get("use_case"))

    buyer = {
        "party_role": "buyer",
        "full_name": "Quinn Buyer",
        "email": "quinn.buyer.jake.local@example.com",
        "is_primary": True,
        "is_decision_maker": True,
        "must_sign": True,
    }
    processor = {
        "party_role": "processor",
        "full_name": "Pat Processor",
        "company": "Local Test Lender",
        "email": "pat.processor.jake.local@example.com",
        "is_primary": True,
    }
    st_b, buyer_row = call("POST", f"/api/v1/transactions/{tx_id}/parties", token, buyer)
    st_p, proc_row = call("POST", f"/api/v1/transactions/{tx_id}/parties", token, processor)
    print(
        "parties",
        json.dumps(
            {
                "buyer": st_b,
                "buyer_flags": {
                    "is_decision_maker": buyer_row.get("is_decision_maker") if isinstance(buyer_row, dict) else buyer_row,
                    "must_sign": buyer_row.get("must_sign") if isinstance(buyer_row, dict) else None,
                },
                "processor": st_p,
                "processor_role": proc_row.get("party_role") if isinstance(proc_row, dict) else proc_row,
            },
            default=str,
        )[:1200],
    )

    st, plan = call("GET", f"/api/v1/transactions/{tx_id}/plan", token)
    header = plan.get("header") if isinstance(plan, dict) else {}
    auto = plan.get("automation") if isinstance(plan, dict) else {}
    print(
        "plan",
        st,
        json.dumps(
            {
                "status": header.get("status") if isinstance(header, dict) else None,
                "tme_stages_line": header.get("tme_stages_line") if isinstance(header, dict) else None,
                "next_action": (header.get("next_action") or {}).get("title") if isinstance(header, dict) else None,
                "posture": auto.get("posture") if isinstance(auto, dict) else None,
                "obligation_autonomy": auto.get("obligation_autonomy") if isinstance(auto, dict) else None,
                "lse_handoff": plan.get("lse_handoff") if isinstance(plan, dict) else None,
            },
            default=str,
        ),
    )

    OUT.joinpath("deal.json").write_text(
        json.dumps({"id": tx_id, "address": payload["address"]}, indent=2),
        encoding="utf-8",
    )
    return 0 if st_b in (200, 201) and st_p in (200, 201) else 4


if __name__ == "__main__":
    sys.exit(main())
