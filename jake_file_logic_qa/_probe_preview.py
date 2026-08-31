"""Dry-run cash appraisal To/CC and amendment extract on staging."""
from __future__ import annotations

import json

from _probe_staging import login, req

CLOSING_NAMES = {
    "Appraisal Ordered",
    "Appraisal Completed",
    "Buyer Closing Information",
    "Seller Closing Information",
    "Seller's Agent Closing Information",
    "Buyer's Agent Closing Information",
}


def main() -> None:
    token = login()
    for uc, ft, rt in (
        ("Sell-Cash", "Cash", "Seller"),
        ("Buy-Cash", "Cash", "Buyer"),
        ("Buy-Fin", "Financed", "Buyer"),
    ):
        st, body = req(
            "POST",
            "/api/v1/transactions/preview-tasks",
            token,
            {
                "address": f"QA {uc} Preview Way",
                "use_case": uc,
                "financing_type": ft,
                "representation_type": rt,
                "has_appraisal": True,
                "contract_acceptance_date": "2026-08-01",
                "closing_date": "2026-09-15",
                "appraisal_expected_date": "2026-08-20",
            },
            timeout=90,
        )
        tasks = (body or {}).get("tasks") or []
        print(uc, st, "n", len(tasks), "err" if st != 200 else "")
        if st != 200:
            print(json.dumps(body, default=str)[:800])
            continue
        for t in tasks:
            if t.get("name") in CLOSING_NAMES:
                print(
                    " ",
                    t.get("name"),
                    "to",
                    t.get("target"),
                    "cc",
                    t.get("cc_targets"),
                )

    st, doc = req(
        "GET",
        "/api/v1/documents/0bc8671c-1633-4c90-bdb2-ab6ccf978cb8",
        token,
    )
    print(
        "amend doc",
        st,
        {k: (doc or {}).get(k) for k in ("doc_type", "status", "ai_confidence", "original_name")},
    )
    ext = (doc or {}).get("ai_extracted_data") or {}
    print("extract keys", list(ext.keys())[:24] if isinstance(ext, dict) else type(ext))
    if isinstance(ext, dict):
        print(json.dumps({k: ext.get(k) for k in list(ext)[:16]}, default=str)[:2000])

    st, status = req("GET", "/api/v1/automation/status", token, timeout=60)
    print("mailbox", (status or {}).get("mailbox_census"))
    print("tenant_tick", (status or {}).get("tenant_tick"))
    print("last_tick_counts", (status or {}).get("last_tick_counts"))
    print("tenants_needing", (status or {}).get("tenants_needing_attention"))
    print("tenant_last_run", (status or {}).get("tenant_last_run_at"))


if __name__ == "__main__":
    main()
