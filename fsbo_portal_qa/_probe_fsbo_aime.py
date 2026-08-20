"""Live probe of FSBO Ask Aime (POST /dashboard/ai-chat)."""
from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "http://127.0.0.1:8000"
FSBO_EMAIL = "yareny.evaly@minafter.com"
PASSWORD = "QWE!@#asd234"


def req(method: str, path: str, token: str | None = None, body: dict | None = None, timeout: int = 60):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = Request(API + path, data=data, headers=headers, method=method)
    try:
        with urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else None
    except HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw) if raw else raw
        except Exception:
            parsed = raw
        return e.code, parsed


def login(email: str) -> str:
    data = urlencode({"username": email, "password": PASSWORD}).encode()
    r = Request(
        API + "/api/v1/users/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(r, timeout=20) as resp:
        return json.loads(resp.read().decode())["access_token"]


def main() -> None:
    tok = login(FSBO_EMAIL)
    print("login ok")
    st, me = req("GET", "/api/v1/users/me", tok)
    print("me", st, (me or {}).get("role"), (me or {}).get("email"))
    st, ov = req("GET", "/api/v1/dashboard/fsbo/overview", tok)
    if isinstance(ov, dict):
        print("overview", st, "n_props", len(ov.get("properties") or []))
    else:
        print("overview", st, ov)

    prompts = [
        "What's missing on my properties?",
        "When do my properties close?",
        "Who is my coordinator and how do I reach them?",
        "What should I do next on my sale?",
        "Tell me about Closing Concierge — what it adds and when it would help me.",
        "What does this step mean?",
    ]
    for prompt in prompts:
        st, body = req(
            "POST",
            "/api/v1/dashboard/ai-chat",
            tok,
            {"message": prompt, "history": []},
        )
        print("---", prompt)
        if not isinstance(body, dict):
            print(st, body)
            continue
        print(
            "status", st,
            "provider", body.get("provider"),
            "err", body.get("error_category"),
            "retry", body.get("error_retryable"),
        )
        print("chips", [a.get("label") for a in (body.get("suggested_actions") or [])])
        print("reply", (body.get("reply") or "")[:700])


if __name__ == "__main__":
    main()
