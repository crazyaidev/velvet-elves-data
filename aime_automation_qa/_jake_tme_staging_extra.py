"""Extra staging snapshots: Dual tasks, header, LSE, parties, verify-deadline body."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

API = "https://api.stage.velvetelves.com"
EMAIL = "crazyaidev20500519@gmail.com"
PW = "QWE!@#asd234"
OUT = Path(__file__).resolve().parent / "artifacts_jake_tme_staging"

DUAL = "f53d0674-8322-4568-9fb9-fae7715d521d"
ACTIVE = "da681bf7-92e8-45b5-b3d0-8f152e461bca"  # 12 Guide Test Way
TERMINATED = "fb22c770-718b-4207-a891-cc44f771b3c4"
LIVE_ACTIVE = "bf1b3bbf-32cd-4215-801e-82eede4c52dd"  # 9052 Sycamore Ridge


def req(method, path, token=None, form=None, data=None):
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
        raw = e.read().decode()[:4000]
        try:
            parsed = json.loads(raw) if raw else {"raw": raw}
        except json.JSONDecodeError:
            parsed = {"raw": raw}
        return e.code, parsed


def login():
    _, body = req("POST", "/api/v1/users/login", form={"username": EMAIL, "password": PW})
    return body["access_token"]


def main():
    token = login()
    dump = {}

    for label, tid in (
        ("dual", DUAL),
        ("guide_test", ACTIVE),
        ("charles_terminated", TERMINATED),
        ("sycamore_active", LIVE_ACTIVE),
    ):
        st, plan = req("GET", f"/api/v1/transactions/{tid}/plan", token)
        header = (plan or {}).get("header") or {}
        auto = (plan or {}).get("automation") or {}
        tracking = (plan or {}).get("tracking_dates") or []
        dump[label] = {
            "plan_http": st,
            "header": {
                k: header.get(k)
                for k in (
                    "display_title",
                    "status",
                    "use_case",
                    "tme_stages",
                    "tme_stages_line",
                    "next_action",
                    "stage_pill",
                    "ai_next_step",
                )
            },
            "automation": {
                k: auto.get(k)
                for k in (
                    "posture",
                    "obligation_autonomy",
                    "obligation_source",
                    "tenant_obligation_default",
                    "needs_you",
                )
            },
            "lse_handoff": (plan or {}).get("lse_handoff"),
            "tracking": [
                {
                    "label": x.get("label") or x.get("field_name"),
                    "field": x.get("field_name") or x.get("field"),
                    "date": x.get("date") or x.get("value"),
                    "provenance": x.get("provenance"),
                }
                for x in tracking
                if isinstance(x, dict)
            ],
            "core_dates": (plan or {}).get("core_dates"),
        }
        st_t, tasks = req("GET", f"/api/v1/tasks/transaction/{tid}?include_ai=true", token)
        names = []
        if isinstance(tasks, list):
            names = [
                {
                    "name": x.get("name"),
                    "target": x.get("target"),
                    "status": x.get("status"),
                    "legacy": ((x.get("metadata_json") or {}) if isinstance(x.get("metadata_json"), dict) else {}).get(
                        "legacy_task_id"
                    ),
                }
                for x in tasks
            ]
        dump[label]["tasks_http"] = st_t
        dump[label]["title_utility"] = [
            n for n in names if n.get("name") and any(w in n["name"].lower() for w in ("title", "utility", "welcome"))
        ]
        st_p, parties = req("GET", f"/api/v1/transactions/{tid}/parties", token)
        plist = parties if isinstance(parties, list) else (parties or {}).get("items") or (parties or {}).get("parties") or []
        dump[label]["parties"] = [
            {
                "role": p.get("party_role") or p.get("role"),
                "name": p.get("full_name") or p.get("name"),
                "is_decision_maker": p.get("is_decision_maker"),
                "must_sign": p.get("must_sign"),
            }
            for p in plist
            if isinstance(p, dict)
        ]
        print(label, "stages", header.get("tme_stages_line"), "next", header.get("next_action"), "parties", len(dump[label]["parties"]))

    st, prev = req(
        "POST",
        "/api/v1/transactions/preview-tasks",
        token,
        data={"use_case": "both_fin", "has_appraisal": True},
    )
    dump["dual_preview_error"] = {"http": st, "body": prev}

    st, keep = req(
        "POST",
        f"/api/v1/transactions/{ACTIVE}/verify-deadline",
        token,
        data={"decision": "keep"},
    )
    dump["verify_keep_guide"] = {"http": st, "body": keep}

    (OUT / "probe_extra.json").write_text(json.dumps(dump, indent=2, default=str), encoding="utf8")
    print("wrote extra")


if __name__ == "__main__":
    main()
