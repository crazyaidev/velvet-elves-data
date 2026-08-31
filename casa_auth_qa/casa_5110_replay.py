"""Replay official ZAP plugin-6 URIs on staging (CASA 5.1.10). Status only. Not an exploit.

Reads Path Traversal instances from the 21 Aug auth XML and repeats those
method+path calls with a staging Bearer. Tokens are not printed. Bodies must
not contain local file dumps.
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
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\5.1.10")
OUT.mkdir(parents=True, exist_ok=True)
EMAIL = os.environ.get("QA_EMAIL", "crazyaidev20500519@gmail.com")
PASSWORD = os.environ.get("QA_PASSWORD")

FILE_MARKERS = (
    "root:x:",
    "daemon:x:",
    "[boot loader]",
    "[fonts]",
    "/etc/passwd",
    "c:\\windows\\system32",
    "nt authority",
    "<?php",
    "#!/bin/sh",
)

OK_STATUS = {200, 400, 403, 404, 405, 409, 415, 422, 500}


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


def has_file_dump(body: str) -> bool:
    low = body.lower()
    return any(m in low for m in FILE_MARKERS)


def parse_instances() -> list[dict]:
    if not XML.is_file():
        raise SystemExit(f"missing ZAP XML: {XML}")
    root = ET.parse(XML).getroot()
    alert = next(
        (el for el in root.iter("alertitem") if (el.findtext("pluginid") or "") == "6"),
        None,
    )
    if alert is None:
        raise SystemExit("no plugin 6 alertitem in XML")
    inst = alert.find("instances")
    rows = []
    for el in list(inst) if inst is not None else []:
        parsed = urlparse((el.findtext("uri") or "").strip())
        rows.append(
            {
                "method": (el.findtext("method") or "GET").strip().upper(),
                "path": parsed.path or "/",
                "query": parsed.query,
                "param": (el.findtext("param") or "").strip(),
                "attack": el.findtext("attack") or "",
            }
        )
    if len(rows) != 4:
        raise SystemExit(f"expected 4 plugin 6 instances, got {len(rows)}")
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
    return json.dumps({param: attack}).encode("utf-8"), "application/json"


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
    if has_file_dump(body):
        return False
    if status == 401:
        return False
    if status == 201:
        return False
    if status == 200:
        text = body.strip()
        return text.startswith("{") or text.startswith("[")
    if status == 500:
        return "internal server error" in body.lower() or "status_code" in body.lower()
    return status in OK_STATUS


def render(results: list[dict], summary: str) -> None:
    w, row_h, header = 1600, 36, 168
    h = header + row_h * (len(results) + 1) + 64
    im = Image.new("RGB", (w, h), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 8), fill=(200, 80, 70))
    d.text((28, 24), "5.1.10  Authenticated replay of ZAP plugin 6 URIs", font=font(20, True), fill=(24, 24, 24))
    d.text(
        (28, 54),
        "Staging api.stage.velvetelves.com  |  scan 33afa2aa  |  Bearer not shown  |  not a new scan",
        font=font(13),
        fill=(80, 80, 80),
    )
    d.text((28, 76), summary, font=font(13), fill=(20, 90, 50))
    d.text(
        (28, 100),
        "ZAP attacks were path segments (team / templates / settings). No local file contents.",
        font=font(12),
        fill=(80, 80, 80),
    )
    y = 128
    for x, label in ((28, "#"), (58, "METH"), (128, "PATH"), (780, "PARAM"), (1020, "HTTP"), (1100, "JSON")):
        d.text((x, y), label, font=font(12, True), fill=(80, 80, 80))
    y = header
    mf = mono(13)
    for i, row in enumerate(results, 1):
        color = (20, 90, 50) if row["ok"] else (140, 40, 40)
        d.text((28, y), f"{i:02d}", font=mf, fill=color)
        d.text((58, y), row["method"][:4], font=mf, fill=color)
        d.text((128, y), row["path_q"][:80], font=mf, fill=color)
        d.text((780, y), row["param"][:28], font=mf, fill=color)
        d.text((1020, y), str(row["status"]), font=mf, fill=color)
        d.text((1100, y), row["snippet"][:62], font=mf, fill=color)
        y += row_h
    d.text((28, h - 36), "31 Aug 2026  |  CASA_5_1_10_auth_replay.png", font=font(12), fill=(80, 80, 80))
    path = OUT / "CASA_5_1_10_auth_replay.png"
    im.save(path, "PNG")
    print("wrote", path)


def main() -> int:
    instances = parse_instances()
    token = login()
    results: list[dict] = []
    try:
        for inst in instances:
            data, ctype = body_for(inst["method"], inst["param"], inst["attack"])
            url = f"{API}{inst['path']}"
            if inst["query"]:
                url = f"{url}?{inst['query']}"
            status, body = http(inst["method"], url, token=token, data=data, ctype=ctype)
            snippet = compact(body, 80)
            path_q = inst["path"] + (f"?{inst['query']}" if inst["query"] else "")
            ok = row_ok(status, body)
            results.append(
                {
                    "method": inst["method"],
                    "path_q": path_q,
                    "param": inst["param"] or "—",
                    "status": status,
                    "snippet": snippet,
                    "ok": ok,
                }
            )
            print(
                f"{len(results):02d} {inst['method']:6} {path_q}  {inst['param']}  {status}  ok={ok}  {snippet[:60]}"
            )
            time.sleep(0.15)
    finally:
        logout(token)

    statuses = {}
    for row in results:
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1
    status_txt = "  ".join(f"{k}x{v}" for k, v in sorted(statuses.items()))
    all_ok = all(r["ok"] for r in results) and len(results) == 4
    summary = (
        f"4/4 replayed. HTTP counts: {status_txt}. "
        f"{'No /etc/passwd or local file dump.' if all_ok else 'A row failed the no-file-dump check.'}"
    )
    render(results, summary)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
