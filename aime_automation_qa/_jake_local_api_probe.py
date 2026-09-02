"""Login smoke + schema probe against local API. Tokens are not printed."""
from __future__ import annotations

import json
import sys
from urllib import error, parse, request

API = "http://127.0.0.1:8000"
EMAIL = "shyna.elene@minafter.com"
PASSWORD = "QWE!@#asd234"


def post_form(path: str, data: dict, token: str | None = None) -> tuple[int, dict]:
    body = parse.urlencode(data).encode()
    req = request.Request(API + path, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"raw": raw[:800]}
        return exc.code, payload


def req(method: str, path: str, token: str, payload: dict | None = None) -> tuple[int, dict | list | None]:
    data = None if payload is None else json.dumps(payload).encode()
    r = request.Request(API + path, data=data, method=method)
    r.add_header("Authorization", f"Bearer {token}")
    if payload is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with request.urlopen(r, timeout=45) as resp:
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
    status, body = post_form("/api/v1/users/login", {"username": EMAIL, "password": PASSWORD})
    keys = sorted(body.keys()) if isinstance(body, dict) else type(body).__name__
    print(f"login_status={status} keys={keys} mfa_required={body.get('mfa_required') if isinstance(body, dict) else None}")
    if status != 200:
        print("login_error", json.dumps(body, default=str)[:800])
        return 1
    if body.get("mfa_required"):
        print("mfa_required=true factor_present=", bool(body.get("mfa_factor_id")))
        return 2
    token = body.get("access_token")
    user = body.get("user") or {}
    print(
        "user_role={role} platform_admin={pa} tenant_id_present={tid}".format(
            role=user.get("role"),
            pa=user.get("is_platform_admin"),
            tid=bool(user.get("tenant_id")),
        )
    )
    st, settings = req("GET", "/api/v1/automation/settings", token)
    if isinstance(settings, dict):
        print(
            "automation_settings",
            st,
            {
                k: settings.get(k)
                for k in (
                    "default_posture",
                    "obligation_autonomy",
                    "playbook_sends_allowed",
                )
                if k in settings or True
            },
        )
    else:
        print("automation_settings", st, type(settings).__name__)

    st, me = req("GET", "/api/v1/users/me", token)
    if isinstance(me, dict):
        print("me", st, {"role": me.get("role"), "is_platform_admin": me.get("is_platform_admin")})

    st, ex = req("GET", "/api/v1/automation/exceptions", token)
    print("exceptions", st, type(ex).__name__ if not isinstance(ex, dict) else list(ex.keys())[:8])
    if st >= 400:
        print("exceptions_body", json.dumps(ex, default=str)[:800])
    return 0


if __name__ == "__main__":
    sys.exit(main())
