"""Authenticated extra probes for 5.1.5 and 5.2.1. Never prints tokens."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from casa_pack_lib import save_probe
from casa_rest_live import API, compact, out

EMAIL = os.environ.get("QA_EMAIL", "crazyaidev20500519@gmail.com")
PASSWORD = os.environ.get("QA_PASSWORD")


def request(method: str, url: str, *, limit: int | None = 220, **kwargs) -> tuple[int, str]:
    headers = {"Accept": "application/json"}
    headers.update(kwargs.pop("headers", {}) or {})
    data = kwargs.pop("data", None)
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            return resp.status, text if limit is None else text[:limit]
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        return exc.code, text if limit is None else text[:limit]


def login() -> str | None:
    body = urllib.parse.urlencode({"username": EMAIL, "password": PASSWORD}).encode()
    st, raw = request(
        "POST",
        f"{API}/api/v1/users/login",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        limit=None,
    )
    try:
        data = json.loads(raw) if raw.strip().startswith("{") else {}
    except json.JSONDecodeError:
        print("login parse failed", st, file=sys.stderr)
        return None
    token = data.get("access_token")
    print(
        "login",
        st,
        "mfa_required",
        data.get("mfa_required"),
        "has_access",
        bool(token),
    )
    return token if st == 200 and token else None


def logout(token: str) -> None:
    st, _ = request(
        "POST",
        f"{API}/api/v1/users/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    print("logout", st)


def probe_515_auth(token: str) -> bool:
    st, body = request(
        "POST",
        f"{API}/api/v1/integrations/webhooks",
        data=json.dumps(
            {
                "target_url": "http://169.254.169.254/latest/meta-data/",
                "event_types": ["contact.created"],
            }
        ).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    ok = st in (400, 403, 422)
    save_probe(
        out("5.1.5"),
        "CASA_5_1_5_ssrf_auth.png",
        "5.1.5  Authenticated webhook create with metadata URL",
        "Bearer session. Expect 400 URL rejected, or 403 if this account is not tenant Admin.",
        [
            (
                "POST /integrations/webhooks  metadata URL + event_types",
                f"HTTP {st}  {compact(body, 110)}",
                ok,
            )
        ],
    )
    return ok and st == 400


def probe_521_415(token: str) -> bool:
    boundary = "----Casa521Deny"
    payload = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="probe.exe"\r\n'
        "Content-Type: application/x-msdownload\r\n"
        "\r\n"
        "MZ\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    st, body = request(
        "POST",
        f"{API}/api/v1/documents/upload",
        data=payload,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {token}",
        },
    )
    ok = st == 415
    save_probe(
        out("5.2.1"),
        "CASA_5_2_1_415.png",
        "5.2.1  Authenticated upload of a disallowed MIME is 415",
        "Tiny dummy bytes. Not malware. MIME application/x-msdownload is not on the allowlist.",
        [
            (
                "POST /documents/upload  probe.exe application/x-msdownload",
                f"HTTP {st}  {compact(body, 110)}",
                ok,
            )
        ],
    )
    return ok


if __name__ == "__main__":
    if not PASSWORD:
        print("Set QA_PASSWORD", file=sys.stderr)
        sys.exit(2)
    token = login()
    if not token:
        save_probe(
            out("5.1.5"),
            "CASA_5_1_5_ssrf_auth.png",
            "5.1.5  Authenticated webhook create was not run",
            "Login did not return an access token.",
            [("POST /users/login", "no access_token", False)],
        )
        save_probe(
            out("5.2.1"),
            "CASA_5_2_1_415.png",
            "5.2.1  Authenticated MIME deny was not run",
            "Login did not return an access token.",
            [("POST /users/login", "no access_token", False)],
        )
        sys.exit(1)
    try:
        a = probe_515_auth(token)
        b = probe_521_415(token)
        print("5.1.5_auth", a)
        print("5.2.1_415", b)
        sys.exit(0 if a and b else 1)
    finally:
        logout(token)
