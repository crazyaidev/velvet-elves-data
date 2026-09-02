"""Inspect open vs completed named emails on the staging test files."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

API = "https://api.stage.velvetelves.com"
EMAIL = "crazyaidev20500519@gmail.com"
PW = "QWE!@#asd234"
FILES = {
    "elm": "3f469ceb-d5d1-490a-8808-c6abd3a8bc46",
    "maple": "9507baaf-ad8b-41ce-912c-6d637fbb9138",
    "cedar": "002b791f-ef34-4b8c-ad45-37479d447019",
    "nocontract": "36507487-da17-4c37-a458-3d6faad3863c",
    "dual": "f53d0674-8322-4568-9fb9-fae7715d521d",
    "confirm": "ff800067-b769-4964-82a3-3855ea94a565",
    "utility": "10e00794-5689-45d0-9c3f-8a165eff85d4",
    "ordertitle": "3d038ddc-697f-45a5-8fd9-668fe94a8022",
}
WANT = {
    "Buyer Welcome",
    "Seller Welcome",
    "Co-op Agent Welcome",
    "Loan Officer Welcome",
    "Order Title",
    "Confirm Title Order",
    "Appraisal Ordered",
    "Deliver Title",
    "Deliver Utility Info",
}


def req(method, path, token=None, form=None):
    headers = {"Accept": "application/json"}
    body = None
    if token:
        headers["Authorization"] = "Bearer " + token
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    r = urllib.request.Request(API + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=60) as resp:
        return json.loads(resp.read().decode())


def main():
    login = req("POST", "/api/v1/users/login", form={"username": EMAIL, "password": PW})
    token = login["access_token"]
    for label, tx_id in FILES.items():
        tasks = req("GET", f"/api/v1/tasks/transaction/{tx_id}?include_ai=true", token)
        print(f"\n=== {label} ===")
        for t in tasks:
            if t.get("name") in WANT:
                print(
                    t.get("name"),
                    t.get("status"),
                    t.get("target"),
                    t.get("automation_level"),
                    "needs" if (t.get("metadata_json") or {}).get("ai_needs_user") else "",
                )


if __name__ == "__main__":
    main()
