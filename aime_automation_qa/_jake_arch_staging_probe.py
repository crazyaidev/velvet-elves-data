"""Read-only staging snapshot for the Jake architecture review. No send."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.stage.velvetelves.com"
EMAIL = "crazyaidev20500519@gmail.com"
PW = "QWE!@#asd234"
OUT = Path(__file__).resolve().parent / "artifacts_feature14_32_staging_deploy" / "jake_arch_probe.json"


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
    except Exception as e:
        code = getattr(e, "code", None)
        raw = ""
        if hasattr(e, "read"):
            try:
                raw = e.read().decode()[:800]
            except Exception:
                raw = str(e)
        return code or 0, {"error": str(e), "raw": raw}


def main():
    st, login = req("POST", "/api/v1/users/login", form={"username": EMAIL, "password": PW})
    token = (login or {}).get("access_token")
    dump = {"login": st, "paths": {}}
    if not token:
        dump["login_body"] = login
        OUT.write_text(json.dumps(dump, indent=2), encoding="utf8")
        print("login failed", st)
        return

    for path in (
        "/api/health",
        "/api/v1/users/me",
        "/api/v1/tenants/current",
        "/api/v1/automation/status",
        "/api/v1/automation/needs-you",
        "/api/v1/ai-suggestions?page=1&page_size=5",
        "/api/v1/dashboard/ai-briefing",
        "/api/v1/dashboard/sidebar-kpis",
        "/api/v1/transactions?page=1&page_size=5",
        "/api/v1/tasks/queue",
    ):
        code, body = req("GET", path, token)
        summary = {"status": code}
        if isinstance(body, dict):
            keys = list(body.keys())[:20]
            summary["keys"] = keys
            for k in (
                "default_posture",
                "posture",
                "scheduler_enabled",
                "library_send_enabled",
                "aime_signature_enabled",
                "inspection_reminder_send_enabled",
                "last_run_at",
            ):
                if k in body:
                    summary[k] = body[k]
            auto = body.get("automation") if isinstance(body.get("automation"), dict) else None
            settings = body.get("settings_json") if isinstance(body.get("settings_json"), dict) else None
            if auto:
                summary["automation"] = {
                    k: auto.get(k)
                    for k in (
                        "default_posture",
                        "scheduler_enabled",
                        "library_send_enabled",
                        "aime_signature_enabled",
                    )
                    if k in auto
                }
            if settings and isinstance(settings.get("automation"), dict):
                summary["settings_automation"] = {
                    k: settings["automation"].get(k)
                    for k in (
                        "default_posture",
                        "scheduler_enabled",
                        "library_send_enabled",
                        "aime_signature_enabled",
                    )
                }
            if "items" in body:
                summary["n_items"] = len(body.get("items") or [])
            if "total" in body:
                summary["total"] = body.get("total")
            if path.endswith("/me"):
                summary["role"] = body.get("role")
                summary["platform"] = body.get("is_platform_admin")
            if "critical" in body or "needs_attention" in body:
                summary["briefing"] = {
                    k: body.get(k)
                    for k in ("critical", "needs_attention", "on_track", "counts")
                    if k in body
                }
        dump["paths"][path] = summary
        print(path, code, {k: v for k, v in summary.items() if k != "keys"})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dump, indent=2), encoding="utf8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
