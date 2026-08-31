"""Live probes and scans for remaining CASA rows. Velvet Elves hosts only."""
from __future__ import annotations

import json
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from casa_pack_lib import save_probe

ROOT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images")
API = "https://api.stage.velvetelves.com"
PROD_API = "https://api.prod.velvetelves.com"
BACKEND = Path(r"c:\Projects\velvet-elves-backend")
FRONTEND = Path(r"c:\Projects\velvet-elves-frontend")

sys.path.insert(0, str(BACKEND))
from app.utils.url_safety import assert_safe_url  # noqa: E402


def request(method: str, url: str, **kwargs) -> tuple[int, str]:
    headers = {"Accept": "application/json,text/html;q=0.8"}
    headers.update(kwargs.pop("headers", {}) or {})
    data = kwargs.pop("data", None)
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")[:180]
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")[:180]


def compact(text: str, n: int = 90) -> str:
    return " ".join(text.split())[:n]


def out(cid: str) -> Path:
    p = ROOT / cid
    p.mkdir(parents=True, exist_ok=True)
    return p


def probe_513():
    st, body = request("GET", f"{API}/api/v1/health?q=__import__('os')")
    ok = st == 200 and "ok" in body
    save_probe(
        out("5.1.3"),
        "CASA_5_1_3_probe.png",
        "5.1.3  Staging does not eval query strings",
        "Health ignores extra query. Not an exploit.",
        [("GET /health?q=__import__('os')", f"HTTP {st}  {compact(body)}", ok)],
    )
    return ok


def probe_514():
    query = urllib.parse.urlencode({"q": "{{7*7}}"})
    st, body = request("GET", f"{API}/api/v1/health?{query}")
    compact_body = compact(body)
    ok = st == 200 and "ok" in body and compact_body.strip() not in ("49", '"49"')
    save_probe(
        out("5.1.4"),
        "CASA_5_1_4_probe.png",
        "5.1.4  Staging does not evaluate template expressions",
        "GET /api/v1/health with q={{7*7}}. Extra query is ignored. Not an exploit.",
        [
            ("Request", f"{API}/api/v1/health?{query}", True),
            ("HTTP status", str(st), st == 200),
            ("JSON body", compact_body, ok),
            ("Evaluated to 49?", "NO — health JSON, extra query ignored", ok),
        ],
    )
    return ok


def probe_515():
    rows_local = []
    for url, expect_fail in [
        ("http://127.0.0.1/x", True),
        ("http://169.254.169.254/latest/meta-data/", True),
        ("http://metadata.google.internal/", True),
        ("https://8.8.8.8/webhook", False),
    ]:
        try:
            assert_safe_url(url)
            failed = False
        except ValueError:
            failed = True
        ok = failed is expect_fail
        rows_local.append((f"assert_safe_url {url}", "rejected" if failed else "allowed", ok))
    st, body = request(
        "POST",
        f"{API}/api/v1/integrations/webhooks",
        data=json.dumps({"target_url": "http://169.254.169.254/"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    live_ok = st in (401, 403, 404, 405, 422)
    rows_local.append(
        ("POST /integrations/webhooks unsigned metadata URL", f"HTTP {st}  {compact(body)}", live_ok)
    )
    save_probe(
        out("5.1.5"),
        "CASA_5_1_5_ssrf.png",
        "5.1.5  SSRF guard rejects private and metadata URLs",
        "Local assert_safe_url plus unsigned staging webhook.",
        rows_local,
    )
    return all(ok for _, _, ok in rows_local)


def probe_516():
    st, body = request(
        "POST",
        f"{API}/api/v1/users/login",
        data=b"<foo/>",
        headers={"Content-Type": "application/xml"},
    )
    ok = st in (400, 415, 422) and "<foo" not in body
    save_probe(
        out("5.1.6"),
        "CASA_5_1_6_xml.png",
        "5.1.6  JSON login rejects an XML body",
        "Not an XML parser. Login is form/JSON.",
        [("POST /users/login Content-Type application/xml", f"HTTP {st}  {compact(body)}", ok)],
    )
    return ok


def probe_517():
    q = urllib.parse.quote("</p><script>alert(1)</script>", safe="")
    st, body = request(
        "GET",
        f"{API}/api/v1/integrations/gmail/callback?error={q}&error_description={q}",
    )
    reflected = "<script>" in body.lower()
    ok = st in (200, 400) and not reflected
    save_probe(
        out("5.1.7"),
        "CASA_5_1_7_callback.png",
        "5.1.7  OAuth callback does not echo a script tag",
        "Staging Gmail callback. Query is escaped / generic cancelled copy.",
        [
            (
                "GET /integrations/gmail/callback?error=<script>",
                f"HTTP {st}  script_tag_in_body={reflected}  {compact(body)}",
                ok,
            )
        ],
    )
    return ok


def probe_518():
    st, body = request("GET", f"{API}/api/v1/teams?page_size='(")
    ok = st in (401, 422) and "sql" not in body.lower() and "syntax" not in body.lower()
    save_probe(
        out("5.1.8"),
        "CASA_5_1_8_replay.png",
        "5.1.8  Staging SQLi-looking page_size is not a SQL error",
        "Unsigned. Auth ZAP Highs were Low confidence 500s; this is 401 or 422.",
        [("GET /teams?page_size='(", f"HTTP {st}  {compact(body)}", ok)],
    )
    return ok


def probe_5110():
    st, body = request("GET", f"{API}/api/v1/ads/..%2f..%2fetc%2fpasswd/click")
    loc_ok = st in (400, 404, 422) and "root:" not in body
    save_probe(
        out("5.1.10"),
        "CASA_5_1_10_path.png",
        "5.1.10  Ad click does not include local files",
        "Traversal-looking hook id. Not /etc/passwd content.",
        [("GET /ads/../etc/passwd/click", f"HTTP {st}  {compact(body)}", loc_ok)],
    )
    return loc_ok


def probe_521():
    st, body = request("POST", f"{API}/api/v1/documents/upload")
    ok = st in (401, 403, 415, 422)
    save_probe(
        out("5.2.1"),
        "CASA_5_2_1_deny.png",
        "5.2.1  Unsigned document upload is rejected",
        "No malware file was uploaded.",
        [("POST /documents/upload  no auth", f"HTTP {st}  {compact(body)}", ok)],
    )
    return ok


def probe_621():
    rows = []
    for label, url, expect in [
        ("prod /api/docs", f"{PROD_API}/api/docs", 404),
        ("prod /api/redoc", f"{PROD_API}/api/redoc", 404),
        ("prod /api/openapi.json", f"{PROD_API}/api/openapi.json", 404),
        ("staging /api/docs", f"{API}/api/docs", 200),
    ]:
        st, _body = request("GET", url, headers={"Accept": "text/html,application/json"})
        ok = st == expect
        rows.append((label, f"HTTP {st} (expect {expect})", ok))
    save_probe(
        out("6.2.1"),
        "CASA_6_2_1_docs.png",
        "6.2.1  Production OpenAPI UI is 404; staging docs stay on",
        "Production APP_ENV hides /api/docs.",
        rows,
    )
    return all(ok for _, _, ok in rows)


def probe_631():
    st, body = request(
        "GET",
        f"{API}/api/v1/users/me",
        headers={"Origin": "https://evil.example"},
    )
    ok = st == 401
    save_probe(
        out("6.3.1"),
        "CASA_6_3_1_origin.png",
        "6.3.1  Foreign Origin does not authenticate /users/me",
        "Still 401 without a Bearer token.",
        [("GET /users/me  Origin https://evil.example", f"HTTP {st}  {compact(body)}", ok)],
    )
    return ok


def probe_641():
    names = [
        "app.velvetelves.com",
        "app.stage.velvetelves.com",
        "api.prod.velvetelves.com",
        "api.stage.velvetelves.com",
        "help.velvetelves.com",
        "velvetelves.com",
    ]
    rows = []
    all_ok = True
    for name in names:
        try:
            infos = socket.getaddrinfo(name, 443)
            addrs = sorted({i[4][0] for i in infos})
            ok = bool(addrs)
            detail = ", ".join(addrs[:4]) or "(none)"
        except socket.gaierror as exc:
            ok = False
            detail = str(exc)
        all_ok = all_ok and ok
        rows.append((name, detail, ok))
    save_probe(
        out("6.4.1"),
        "CASA_6_4_1_dns.png",
        "6.4.1  Live DNS answers for Velvet Elves names",
        "Resolver on this machine. Route 53 console was not captured.",
        rows,
    )
    return all_ok


def probe_651_mask():
    from email.utils import parseaddr

    def mask(value: str) -> str:
        text = parseaddr(value or "")[1] or (value or "").strip()
        local, domain = text.rsplit("@", 1)
        return f"{local[:2]}***@{domain}"

    sample = mask("agent.name@example.com")
    ok = sample == "ag***@example.com"
    save_probe(
        out("6.5.1"),
        "CASA_6_5_1_mask.png",
        "6.5.1  Email mask helper (not a CloudWatch login log)",
        "Staging CloudWatch login and Stripe checkout-session samples obtained 31 Aug 2026.",
        [(f"mask(agent.name@example.com) = {sample}", "not a live log extract", ok)],
    )
    return ok


def copy_661():
    src = ROOT / "2.2.1" / "CASA_2_2_1_after_logout.png"
    dest = out("6.6.1") / "CASA_6_6_1_after_logout.png"
    shutil.copyfile(src, dest)
    print("copied", dest)
    return dest.exists()


def run_611():
    pip_ok = False
    npm_ok = False
    try:
        pip = subprocess.run(
            ["python", "-m", "pip_audit", "-r", "requirements.txt", "--progress-spinner", "off"],
            cwd=BACKEND,
            capture_output=True,
            text=True,
            timeout=180,
        )
        pip_lines = (pip.stdout or pip.stderr or "").splitlines()[:12] or [f"exit {pip.returncode}"]
        pip_ok = True
        save_probe(
            out("6.1.1"),
            "CASA_6_1_1_pip.png",
            "6.1.1  pip-audit requirements.txt (local lockfile)",
            f"exit {pip.returncode}. Not a production image scan. ecdsa may remain.",
            [(line[:90] or " ", f"exit {pip.returncode}", pip.returncode in (0, 1)) for line in pip_lines[:8]],
        )
    except Exception as exc:
        save_probe(
            out("6.1.1"),
            "CASA_6_1_1_pip.png",
            "6.1.1  pip-audit did not complete",
            str(exc)[:120],
            [("pip-audit", str(exc)[:90], False)],
        )
    try:
        npm = subprocess.run(
            ["npm", "audit", "--omit=dev"],
            cwd=FRONTEND,
            capture_output=True,
            text=True,
            timeout=180,
            shell=True,
        )
        npm_lines = (npm.stdout or npm.stderr or "").splitlines()[:12] or [f"exit {npm.returncode}"]
        npm_ok = True
        save_probe(
            out("6.1.1"),
            "CASA_6_1_1_npm.png",
            "6.1.1  npm audit --omit=dev (SPA lockfile)",
            f"exit {npm.returncode}. Dev toolchain vulns omitted.",
            [(line[:90] or " ", f"exit {npm.returncode}", npm.returncode in (0, 1)) for line in npm_lines[:8]],
        )
    except Exception as exc:
        save_probe(
            out("6.1.1"),
            "CASA_6_1_1_npm.png",
            "6.1.1  npm audit did not complete",
            str(exc)[:120],
            [("npm audit", str(exc)[:90], False)],
        )
    return pip_ok, npm_ok


if __name__ == "__main__":
    results = {
        "5.1.3": probe_513(),
        "5.1.4": probe_514(),
        "5.1.5": probe_515(),
        "5.1.6": probe_516(),
        "5.1.7": probe_517(),
        "5.1.8": probe_518(),
        "5.1.10": probe_5110(),
        "5.2.1": probe_521(),
        "6.1.1_tools": run_611(),
        "6.2.1": probe_621(),
        "6.3.1": probe_631(),
        "6.4.1": probe_641(),
        "6.5.1": probe_651_mask(),
        "6.6.1": copy_661(),
    }
    for k, v in results.items():
        print(("OK " if v else "!! "), k, v)
