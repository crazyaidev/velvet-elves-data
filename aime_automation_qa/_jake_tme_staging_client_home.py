"""Dump client home payload + team-lead obligation_autonomy."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.stage.velvetelves.com"
PW = "QWE!@#asd234"
OUT = Path(__file__).resolve().parent / "artifacts_jake_tme_staging"


def req(method, path, token=None, form=None):
    headers = {"Accept": "application/json"}
    body = None
    if token:
        headers["Authorization"] = "Bearer " + token
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    r = urllib.request.Request(API + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=45) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def login(email):
    return req("POST", "/api/v1/users/login", form={"username": email, "password": PW})["access_token"]


def main():
    token = login("ellenore.zynique@minafter.com")
    dash = req("GET", "/api/v1/dashboard/client", token)
    home = dash.get("home") or {}
    slim = {
        "tx_count": len(dash.get("transactions") or []),
        "home_keys": list(home.keys())[:30] if isinstance(home, dict) else home,
        "next_action": home.get("next_action") if isinstance(home, dict) else None,
        "hero": (home.get("hero") or {}).get("title") if isinstance(home, dict) else None,
        "boundary_notice": dash.get("boundary_notice"),
        "agent_card": {k: (dash.get("agent_card") or {}).get(k) for k in ("name", "role")}
        if isinstance(dash.get("agent_card"), dict)
        else dash.get("agent_card"),
    }
    (OUT / "client_dashboard.json").write_text(json.dumps(slim, indent=2, default=str), encoding="utf8")
    print(json.dumps(slim, indent=2, default=str)[:2000])

    tl = login("keylan.symir@minafter.com")
    settings = req("GET", "/api/v1/automation/settings", tl)
    print("teamlead obligation", settings.get("obligation_autonomy"), "posture", settings.get("default_posture"))


if __name__ == "__main__":
    main()
