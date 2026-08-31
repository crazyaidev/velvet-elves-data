"""Verify the two staging deploys: CD omit on closing-info, automation status healthy."""
from __future__ import annotations

import json

from _probe_staging import login, req

CLOSING = (
    "Buyer Closing Information",
    "Seller Closing Information",
    "Seller's Agent Closing Information",
    "Buyer's Agent Closing Information",
)


def main() -> None:
    token = login()
    print("login ok")
    st, health = req("GET", "/api/v1/health")
    print("health", st, health)
    st, status = req("GET", "/api/v1/automation/status", token, timeout=60)
    print(
        "status",
        st,
        {
            "scheduler_healthy": (status or {}).get("scheduler_healthy"),
            "scheduler_state": (status or {}).get("scheduler_state"),
            "last_tick_at": (status or {}).get("last_tick_at"),
        },
    )

    st, listed = req("GET", "/api/v1/transactions?page=1&page_size=50", token, timeout=60)
    txs = (listed or {}).get("items") or []
    print("tx n", len(txs))
    plans = []
    docs_cd = []
    for t in txs:
        tid = t["id"]
        st, docs = req("GET", f"/api/v1/documents/transaction/{tid}", token)
        cd = []
        if isinstance(docs, list):
            for d in docs:
                name = str(d.get("original_name") or d.get("file_name") or "")
                dtype = str(d.get("doc_type") or "")
                if "closing_disclosure" in dtype.lower() or "closing disclosure" in name.lower():
                    cd.append({"name": name, "doc_type": dtype, "id": d.get("id")})
        if cd:
            docs_cd.append({"tx": t.get("address"), "cd": cd})
        st, tasks = req("GET", f"/api/v1/tasks/transaction/{tid}", token)
        if not isinstance(tasks, list):
            continue
        for x in tasks:
            name = str(x.get("name") or "")
            if name not in CLOSING and "closing information" not in name.lower():
                continue
            st_ep, eplan = req("GET", f"/api/v1/tasks/{x['id']}/email-plan", token)
            atts = []
            if isinstance(eplan, dict):
                atts = list(eplan.get("attachments") or [])
                for leg in eplan.get("legs") or []:
                    atts.extend(leg.get("attachments") or [])
            row = {
                "tx": t.get("address"),
                "task": name,
                "status": x.get("status"),
                "http": st_ep,
                "can_send": (eplan or {}).get("can_send") if isinstance(eplan, dict) else None,
                "attachments": atts,
                "summary": ((eplan or {}).get("summary") if isinstance(eplan, dict) else None),
            }
            plans.append(row)
            att_blob = json.dumps(atts).lower()
            cd_hit = "closing disclosure" in att_blob or "closing_disclosure" in att_blob
            print(
                "PLAN",
                "FAIL" if cd_hit else "PASS",
                name,
                t.get("address"),
                "atts",
                atts,
            )
    print("cd docs", json.dumps(docs_cd, indent=2)[:2000])
    print("plans n", len(plans))


if __name__ == "__main__":
    main()
