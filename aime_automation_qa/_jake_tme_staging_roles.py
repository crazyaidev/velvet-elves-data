"""Login as staging client and dump dashboard. Also team lead me."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
import urllib.error
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
    try:
        with urllib.request.urlopen(r, timeout=45) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()[:3000]
        try:
            parsed = json.loads(raw) if raw else {"raw": raw}
        except json.JSONDecodeError:
            parsed = {"raw": raw}
        return e.code, parsed
    except Exception as e:
        return 0, {"error": str(e)}


def login(email):
    st, body = req("POST", "/api/v1/users/login", form={"username": email, "password": PW})
    return st, body


def slim(user):
    if not isinstance(user, dict):
        return user
    return {
        k: user.get(k)
        for k in ("email", "role", "full_name", "is_platform_admin", "onboarding_completed", "tenant_id")
    }


def main():
    dump = {}
    for email, paths in (
        (
            "ellenore.zynique@minafter.com",
            [
                "/api/v1/users/me",
                "/api/v1/dashboard/client",
                "/api/v1/dashboard/client-home",
                "/api/v1/client/home",
            ],
        ),
        (
            "keylan.symir@minafter.com",
            ["/api/v1/users/me", "/api/v1/transactions?page=1&page_size=5", "/api/v1/automation/settings"],
        ),
        (
            "brevyn.joshawn@minafter.com",
            ["/api/v1/users/me"],
        ),
        (
            "enrico.dasean@minafter.com",
            ["/api/v1/users/me"],
        ),
    ):
        st, body = login(email)
        row = {"login": st, "mfa": (body or {}).get("mfa_required") if isinstance(body, dict) else None, "user": slim((body or {}).get("user") if isinstance(body, dict) else {})}
        token = (body or {}).get("access_token") if isinstance(body, dict) else None
        print(email, "login", st, row["user"], "token", bool(token))
        if token:
            for p in paths:
                code, payload = req("GET", p, token)
                keys = list(payload.keys())[:15] if isinstance(payload, dict) else type(payload).__name__
                row[p] = {"http": code, "keys": keys}
                if isinstance(payload, dict) and code >= 400:
                    row[p]["body"] = payload
                print(" ", p, code, keys)
        dump[email] = row
    (OUT / "probe_roles.json").write_text(json.dumps(dump, indent=2, default=str), encoding="utf8")


if __name__ == "__main__":
    main()
