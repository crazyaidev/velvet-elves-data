"""One-shot probe of tessa.grant vendor-portal APIs (local)."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

EMAIL = "tessa.grant@minafter.com"
PASSWORD = "QWE!@#asd234"
BASE = "http://127.0.0.1:8000"


def post_login() -> str:
    body = urllib.parse.urlencode({"username": EMAIL, "password": PASSWORD}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/v1/users/login",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())["access_token"]


def get(path: str, token: str):
    req = urllib.request.Request(f"{BASE}{path}", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def main() -> None:
    token = post_login()
    tasks = get("/api/v1/vendor-portal/tasks", token)["tasks"]
    print("TASK_COUNT", len(tasks))
    for t in tasks:
        print(
            f"{t['family']:8} {t['group']:8} {t['status']:12} "
            f"{t['name'][:72]} | ms={t.get('milestone_label')!r}"
        )
    tid = "29e4c7f3-de4a-430b-ac11-9284c8bdebab"
    detail = get(f"/api/v1/vendor-portal/files/{tid}", token)
    print("\nCONTACTS")
    for c in detail.get("contacts", []):
        print(json.dumps(c, default=str))
    print("\nMILESTONES", detail.get("file", {}).get("milestones"))
    print("KEY_DATES", detail.get("key_dates"))
    print("CAN_ADD", detail.get("can_add_contact_group"))
    print(
        "DOCS",
        len(detail.get("documents") or []),
        "TASKS",
        len(detail.get("tasks") or []),
        "ACTIVITY",
        len(detail.get("activity") or []),
    )
    ov = get("/api/v1/vendor-portal/overview", token)
    print("\nSTATS", ov.get("stats"), "FAMILY", ov.get("scope_family"), "ROLE", ov.get("role_label"))
    print("NEXT", (ov.get("files") or [{}])[0].get("next_step"))
    print("MILESTONE_BADGE", (ov.get("files") or [{}])[0].get("milestone_label"))


if __name__ == "__main__":
    main()
