"""Replay official ZAP 40018 URIs on staging (CASA 5.1.8). Status only. Not an exploit.

Reads plugin 40018 instances from the 21 Aug auth XML and repeats those
method+path calls with a staging Bearer. Attack strings stay in memory from
the XML; they are not written to git or the PNG. Tokens are not printed.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont

API = "https://api.stage.velvetelves.com"
XML = Path(
    r"c:\Projects\velvet-elves-data\casa_al1_evidence\2026-08-21"
    r"\dast\api-auth-33afa2aa\extracted\zap-casa-api-auth.xml"
)
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\5.1.8")
OUT.mkdir(parents=True, exist_ok=True)
EMAIL = os.environ.get("QA_EMAIL", "crazyaidev20500519@gmail.com")
PASSWORD = os.environ.get("QA_PASSWORD")

SQL_MARKERS = (
    "sqlstate",
    "syntax error at",
    "unterminated quoted",
    "psycopg",
    "sqlalchemy.exc",
    'relation "',
    'column "',
    "traceback (most recent",
    "mysql",
    "sqlite",
    "ora-",
    "pg_catalog",
)

OK_STATUS = {400, 403, 404, 405, 409, 415, 422, 500}


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def mono(size: int):
    p = Path(r"C:\Windows\Fonts\consola.ttf")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return font(size)


def compact(text: str, n: int = 80) -> str:
    return " ".join((text or "").split())[:n]


def has_sql_text(body: str) -> bool:
    low = body.lower()
    return any(m in low for m in SQL_MARKERS)


def parse_instances() -> list[dict]:
    if not XML.is_file():
        raise SystemExit(f"missing ZAP XML: {XML}")
    root = ET.parse(XML).getroot()
    alert = next(
        (el for el in root.iter("alertitem") if (el.findtext("pluginid") or "") == "40018"),
        None,
    )
    if alert is None:
        raise SystemExit("no plugin 40018 alertitem in XML")
    inst = alert.find("instances")
    rows = []
    for el in list(inst) if inst is not None else []:
        raw = (el.findtext("uri") or "").strip()
        parsed = urlparse(raw)
        path = parsed.path or "/"
        query = parsed.query
        method = (el.findtext("method") or "GET").strip().upper()
        param = (el.findtext("param") or "").strip()
        attack = el.findtext("attack") or ""
        rows.append(
            {
                "method": method,
                "path": path,
                "query": query,
                "param": param,
                "attack": attack,
            }
        )
    if len(rows) != 28:
        raise SystemExit(f"expected 28 plugin 40018 instances, got {len(rows)}")
    return rows


def http(method: str, url: str, *, token: str, data: bytes | None, ctype: str | None) -> tuple[int, str]:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    if ctype:
        headers["Content-Type"] = ctype
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def body_for(method: str, param: str, attack: str) -> tuple[bytes | None, str | None]:
    if method == "GET" or not param:
        return None, None
    if param.endswith("[0]"):
        key = param[: -len("[0]")]
        payload = {key: [attack]}
    else:
        payload = {param: attack}
    return json.dumps(payload).encode("utf-8"), "application/json"


def login() -> str:
    if not PASSWORD:
        raise SystemExit("Set QA_PASSWORD")
    data = urllib.parse.urlencode({"username": EMAIL, "password": PASSWORD}).encode()
    req = urllib.request.Request(
        f"{API}/api/v1/users/login",
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    try:
        parsed = json.loads(raw) if raw.strip().startswith("{") else {}
    except json.JSONDecodeError:
        parsed = {}
    token = parsed.get("access_token")
    if status != 200 or not isinstance(token, str):
        raise SystemExit(f"login failed status={status} mfa={parsed.get('mfa_required')}")
    return token


def logout(token: str) -> None:
    try:
        http("POST", f"{API}/api/v1/users/logout", token=token, data=None, ctype=None)
    except Exception:
        pass


def row_ok(status: int, body: str) -> bool:
    if has_sql_text(body):
        return False
    if status == 401:
        return False
    if status in OK_STATUS:
        if status == 500:
            return "internal server error" in body.lower() or "status_code" in body.lower()
        return True
    if status == 200:
        text = body.strip()
        return text.startswith("{") or text.startswith("[")
    return False


def render(results: list[dict], summary: str) -> None:
    w, row_h, header = 1600, 26, 168
    h = header + row_h * (len(results) + 2) + 56
    im = Image.new("RGB", (w, h), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 8), fill=(200, 80, 70))
    d.text((28, 24), "5.1.8  Authenticated replay of ZAP 40018 URIs", font=font(20, True), fill=(24, 24, 24))
    d.text(
        (28, 54),
        "Staging api.stage.velvetelves.com  |  scan 33afa2aa  |  Bearer not shown  |  not a new scan",
        font=font(13),
        fill=(80, 80, 80),
    )
    d.text((28, 76), summary, font=font(13), fill=(20, 90, 50))
    d.text(
        (28, 100),
        "Path + param + status + first 80 chars of JSON. Attack strings from the XML are not drawn.",
        font=font(12),
        fill=(80, 80, 80),
    )
    cols = [(28, "#"), (58, "METH"), (128, "PATH"), (720, "PARAM"), (960, "HTTP"), (1030, "JSON")]
    y = 128
    for x, label in cols:
        d.text((x, y), label, font=font(12, True), fill=(80, 80, 80))
    y = header
    mf = mono(12)
    for i, row in enumerate(results, 1):
        color = (20, 90, 50) if row["ok"] else (140, 40, 40)
        d.text((28, y), f"{i:02d}", font=mf, fill=color)
        d.text((58, y), row["method"][:4], font=mf, fill=color)
        d.text((128, y), row["path"][:72], font=mf, fill=color)
        d.text((720, y), row["param"][:28], font=mf, fill=color)
        d.text((960, y), str(row["status"]), font=mf, fill=color)
        d.text((1030, y), row["snippet"][:70], font=mf, fill=color)
        y += row_h
    d.text((28, h - 36), "31 Aug 2026  |  CASA_5_1_8_auth_replay.png", font=font(12), fill=(80, 80, 80))
    path = OUT / "CASA_5_1_8_auth_replay.png"
    im.save(path, "PNG")
    print("wrote", path)


def main() -> int:
    instances = parse_instances()
    token = login()
    results: list[dict] = []
    try:
        for inst in instances:
            data, ctype = body_for(inst["method"], inst["param"], inst["attack"])
            if inst["method"] == "GET":
                url = f"{API}{inst['path']}"
                if inst["query"]:
                    url = f"{url}?{inst['query']}"
            else:
                url = f"{API}{inst['path']}"
                if inst["query"]:
                    url = f"{url}?{inst['query']}"
            status, body = http(inst["method"], url, token=token, data=data, ctype=ctype)
            snippet = compact(body, 80)
            ok = row_ok(status, body)
            results.append(
                {
                    "method": inst["method"],
                    "path": inst["path"],
                    "param": inst["param"] or "—",
                    "status": status,
                    "snippet": snippet,
                    "ok": ok,
                }
            )
            print(
                f"{len(results):02d} {inst['method']:6} {inst['path']}  {inst['param']}  {status}  ok={ok}  {snippet[:60]}"
            )
            time.sleep(0.15)
    finally:
        logout(token)

    statuses = {}
    for row in results:
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1
    status_txt = "  ".join(f"{k}x{v}" for k, v in sorted(statuses.items()))
    all_ok = all(r["ok"] for r in results) and len(results) == 28
    leaks = sum(1 for r in results if not r["ok"])
    summary = (
        f"28/28 replayed. HTTP counts: {status_txt}. "
        f"{'No SQLSTATE / table names / syntax-error text.' if all_ok else f'{leaks} row(s) failed the no-SQL-text check.'}"
    )
    render(results, summary)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
