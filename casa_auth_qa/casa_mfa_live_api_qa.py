"""RAM-light live MFA QA: HTTP only, no Chrome/Playwright.

    $env:QA_PASSWORD='…'
    python casa_mfa_live_api_qa.py

Optional:
    QA_EMAIL, QA_API (default http://127.0.0.1:8000), QA_BACKEND_ENV
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

EMAIL = os.environ.get("QA_EMAIL", "shyna.elene@minafter.com")
PASSWORD = os.environ.get("QA_PASSWORD")
API = os.environ.get("QA_API", "http://127.0.0.1:8000").rstrip("/")
BACKEND_ENV = Path(
    os.environ.get(
        "QA_BACKEND_ENV",
        r"C:\Projects\velvet-elves-backend\.env",
    )
)
USER_ID = os.environ.get("QA_USER_ID", "fca6fa25-ab75-4572-9c06-fec36f1e3581")

findings: list[tuple[str, str, str]] = []


def log(check_id: str, result: str, details: str = "") -> None:
    findings.append((check_id, result, details))
    extra = f" — {details[:400]}" if details else ""
    print(f"[{result}] {check_id}{extra}", flush=True)


def jwt_claim(token: str, name: str):
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    data = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")))
    return data.get(name)


def totp(secret: str, now: float | None = None) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    clean = str(secret).replace(" ", "").replace("=", "").upper()
    bits = "".join(f"{alphabet.index(ch):05b}" for ch in clean if ch in alphabet)
    raw = bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits) - len(bits) % 8, 8))
    counter = int((time.time() if now is None else now) // 30)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(raw, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (
        ((digest[offset] & 0x7F) << 24)
        | ((digest[offset + 1] & 0xFF) << 16)
        | ((digest[offset + 2] & 0xFF) << 8)
        | (digest[offset + 3] & 0xFF)
    )
    return f"{code % 1_000_000:06d}"


def wait_next_totp_window() -> None:
    remain = 30 - (time.time() % 30) + 1.2
    print(f"(waiting {remain:.1f}s for a fresh TOTP window)", flush=True)
    time.sleep(remain)


def request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    json_body: dict | None = None,
    form: dict | None = None,
    extra_headers: dict[str, str] | None = None,
    timeout: int = 45,
) -> tuple[int, object]:
    url = path if path.startswith("http") else f"{API}{path}"
    headers = {"Accept": "application/json"}
    data = None
    if form is not None:
        data = urllib.parse.urlencode(form).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            status = resp.status
    except urllib.error.HTTPError as exc:
        body = exc.read()
        status = exc.code
    if not body:
        return status, None
    try:
        return status, json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return status, body.decode("utf-8", errors="replace")[:500]


def load_dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def admin_delete_all_factors(reason: str) -> None:
    env = load_dotenv(BACKEND_ENV)
    supabase_url = (env.get("SUPABASE_URL") or "").rstrip("/")
    service_key = env.get("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not supabase_url or not service_key:
        log("cleanup", "FAIL", "backend .env missing SUPABASE_URL or service role key")
        return
    admin_headers = {"apikey": service_key}
    status, body = request(
        "GET",
        f"{supabase_url}/auth/v1/admin/users/{USER_ID}",
        token=service_key,
        extra_headers=admin_headers,
    )
    if status != 200 or not isinstance(body, dict):
        log("cleanup", "FAIL", f"admin user GET {status}")
        return
    factors = body.get("factors") or []
    for factor in factors:
        fid = factor.get("id")
        if not fid:
            continue
        del_status, _ = request(
            "DELETE",
            f"{supabase_url}/auth/v1/admin/users/{USER_ID}/factors/{fid}",
            token=service_key,
            extra_headers=admin_headers,
        )
        log(
            "cleanup",
            "PASS" if del_status in (200, 204) else "FAIL",
            f"{reason}: deleted factor {fid[:8]}… status={del_status}",
        )


def login() -> dict:
    status, body = request(
        "POST",
        "/api/v1/users/login",
        form={"username": EMAIL, "password": PASSWORD},
    )
    if status != 200 or not isinstance(body, dict) or not body.get("access_token"):
        raise SystemExit(f"login failed status={status} body={body}")
    return body


def error_code(body: object) -> str:
    if isinstance(body, dict):
        detail = body.get("detail")
        if isinstance(detail, dict):
            return str(detail.get("error_code") or "")
        if isinstance(detail, str):
            return detail
    return str(body)[:200]


def main() -> int:
    if not PASSWORD:
        print("Set QA_PASSWORD before running this harness.", file=sys.stderr)
        return 2

    health, _ = request("GET", "/health")
    log("health", "PASS" if health == 200 else "FAIL", f"status={health}")
    if health != 200:
        return 1

    session = login()
    token = str(session["access_token"])
    aal = jwt_claim(token, "aal")
    user = session.get("user") or {}
    log(
        "login",
        "PASS",
        f"mfa_required={session.get('mfa_required')} aal={aal} "
        f"platform={user.get('is_platform_admin')}",
    )

    if session.get("mfa_required") or aal == "aal2":
        log(
            "preexisting_mfa",
            "WARN",
            "account already had MFA or aal2; clearing factors so QA can enroll cleanly",
        )
        admin_delete_all_factors("pre-test leftover")
        session = login()
        token = str(session["access_token"])
        aal = jwt_claim(token, "aal")
        log(
            "login_after_cleanup",
            "PASS" if not session.get("mfa_required") else "FAIL",
            f"mfa_required={session.get('mfa_required')} aal={aal}",
        )

    plat_status, plat_body = request("GET", "/api/v1/platform/users", token=token)
    log(
        "platform_aal1_blocked",
        "PASS" if plat_status == 403 and error_code(plat_body) == "mfa_required" else "FAIL",
        f"status={plat_status} code={error_code(plat_body)}",
    )

    enroll_status, enroll = request("POST", "/api/v1/users/mfa/enroll", token=token, json_body={})
    if enroll_status != 200 or not isinstance(enroll, dict) or not enroll.get("secret"):
        log("enroll", "FAIL", f"status={enroll_status} body={enroll}")
        admin_delete_all_factors("enroll failed leftover")
        return 1
    factor_id = str(enroll["factor_id"])
    secret = str(enroll["secret"])
    log(
        "enroll",
        "PASS",
        f"factor={factor_id[:8]}… has_qr={bool(enroll.get('qr_code'))} "
        f"has_uri={bool(enroll.get('uri'))}",
    )

    listed_status, listed = request("GET", "/api/v1/users/mfa/factors", token=token)
    statuses = []
    if isinstance(listed, dict):
        statuses = [f.get("status") for f in (listed.get("factors") or [])]
    log(
        "factors_unverified",
        "PASS" if listed_status == 200 and "unverified" in statuses else "FAIL",
        f"status={listed_status} factors={statuses}",
    )

    code = totp(secret)
    verify_status, verified = request(
        "POST",
        "/api/v1/users/mfa/verify",
        token=token,
        json_body={"factor_id": factor_id, "code": code},
    )
    if verify_status != 200 or not isinstance(verified, dict) or not verified.get("access_token"):
        log("verify", "FAIL", f"status={verify_status} body={verified}")
        admin_delete_all_factors("verify failed leftover")
        return 1
    aal2_token = str(verified["access_token"])
    aal2 = jwt_claim(aal2_token, "aal")
    log("verify", "PASS" if aal2 == "aal2" else "FAIL", f"aal={aal2}")

    plat2_status, plat2_body = request(
        "GET", "/api/v1/platform/users", token=aal2_token
    )
    log(
        "platform_aal2_open",
        "PASS" if plat2_status == 200 else "FAIL",
        f"status={plat2_status} body_type={type(plat2_body).__name__}",
    )

    del_status, del_body = request(
        "DELETE", f"/api/v1/users/mfa/factors/{factor_id}", token=aal2_token
    )
    log(
        "delete_verified_blocked",
        "PASS" if del_status == 403 and "mfa_reauth_required" in error_code(del_body) else "FAIL",
        f"status={del_status} code={error_code(del_body)}",
    )

    empty_status, empty_body = request(
        "POST", "/api/v1/users/mfa/disable", token=aal2_token, json_body={}
    )
    log(
        "disable_requires_code",
        "PASS" if empty_status == 422 else "FAIL",
        f"status={empty_status} body={empty_body}",
    )

    bad_status, bad_body = request(
        "POST",
        "/api/v1/users/mfa/disable",
        token=aal2_token,
        json_body={"code": "000000"},
    )
    log(
        "disable_wrong_code",
        "PASS" if bad_status in (400, 401, 403) else "FAIL",
        f"status={bad_status} code={error_code(bad_body)}",
    )

    wait_next_totp_window()
    disable_status, disable_body = request(
        "POST",
        "/api/v1/users/mfa/disable",
        token=aal2_token,
        json_body={"code": totp(secret)},
    )
    log(
        "disable_with_code",
        "PASS" if disable_status == 204 else "FAIL",
        f"status={disable_status} body={disable_body}",
    )

    if disable_status != 204:
        admin_delete_all_factors("disable failed leftover")

    stale_status, stale_body = request(
        "GET", "/api/v1/platform/users", token=aal2_token
    )
    log(
        "stale_aal2_blocked",
        "PASS" if stale_status == 403 and error_code(stale_body) == "mfa_required" else "FAIL",
        f"status={stale_status} code={error_code(stale_body)}",
    )

    again = login()
    again_token = str(again["access_token"])
    log(
        "login_after_disable",
        "PASS" if not again.get("mfa_required") else "FAIL",
        f"mfa_required={again.get('mfa_required')} aal={jwt_claim(again_token, 'aal')}",
    )

    factors_status, factors_body = request(
        "GET", "/api/v1/users/mfa/factors", token=again_token
    )
    leftover = []
    if isinstance(factors_body, dict):
        leftover = factors_body.get("factors") or []
    log(
        "no_leftover_factors",
        "PASS" if factors_status == 200 and leftover == [] else "FAIL",
        f"status={factors_status} count={len(leftover)}",
    )
    if leftover:
        admin_delete_all_factors("post-test leftover")

    failed = [f for f in findings if f[1] == "FAIL"]
    print("", flush=True)
    print(
        f"{len(findings) - len(failed)}/{len(findings)} checks passed, "
        f"{len(failed)} failed",
        flush=True,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
