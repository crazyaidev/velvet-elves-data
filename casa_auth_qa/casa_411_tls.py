"""Production TLS / HSTS on Velvet Elves hosts (CASA 4.1.1). Not Qualys SSL Labs."""
from __future__ import annotations

import socket
import ssl
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\4.1.1")
OUT.mkdir(parents=True, exist_ok=True)

# ok=True green, False red. Warnings use ok=False with honest wording.


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def header(headers: dict[str, str], name: str) -> str:
    lower = name.lower()
    for key, value in headers.items():
        if key.lower() == lower:
            return value
    return "(absent)"


def tls_handshake(host: str, *, only: ssl.TLSVersion | None = None) -> dict[str, str]:
    ctx = ssl.create_default_context()
    if only is not None:
        ctx.minimum_version = only
        ctx.maximum_version = only
    with socket.create_connection((host, 443), timeout=20) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert() or {}
            issuer = ""
            for rdn in cert.get("issuer", ()):
                for key, value in rdn:
                    if key == "organizationName":
                        issuer = value
            cipher = ssock.cipher()
            return {
                "version": ssock.version() or "(unknown)",
                "cipher": cipher[0] if cipher else "(unknown)",
                "issuer": issuer or "(unknown)",
            }


def try_legacy_tls(host: str, version: ssl.TLSVersion) -> str:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = version
    ctx.maximum_version = version
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection((host, 443), timeout=12) as sock:
            with ctx.wrap_socket(sock, server_hostname=host):
                return "accepted"
    except Exception:
        return "rejected"


def https_get(url: str) -> tuple[int, str, str]:
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "*/*", "User-Agent": "VelvetElves-CASA-4.1.1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            headers = {k: v for k, v in resp.headers.items()}
            return resp.status, header(headers, "Strict-Transport-Security"), header(headers, "Location")
    except urllib.error.HTTPError as exc:
        headers = {k: v for k, v in exc.headers.items()}
        return exc.code, header(headers, "Strict-Transport-Security"), header(headers, "Location")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def http_get(url: str) -> tuple[int, str, str, str]:
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "VelvetElves-CASA-4.1.1"},
    )
    try:
        with opener.open(req, timeout=20) as resp:
            headers = {k: v for k, v in resp.headers.items()}
            body = resp.read(60).decode("utf-8", errors="replace")
            return resp.status, header(headers, "Location"), header(headers, "Content-Type"), body
    except urllib.error.HTTPError as exc:
        headers = {k: v for k, v in exc.headers.items()}
        body = exc.read(60).decode("utf-8", errors="replace")
        return exc.code, header(headers, "Location"), header(headers, "Content-Type"), body


def render(lines: list[tuple[str, bool]]) -> None:
    W, H = 1400, 1180
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "4.1.1  Production TLS on Velvet Elves hosts (not Qualys SSL Labs)",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "Live handshake 31 Aug 2026. Green = measured. Red = HTTP still reaches the API.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 118
    for line, ok in lines:
        color = (20, 90, 50) if ok else (140, 40, 40)
        d.text((48, y), line, font=font(15), fill=color)
        y += 28
    d.text(
        (48, H - 48),
        "production  |  CASA_4_1_1_tls  |  31 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_4_1_1_tls.png"
    im.save(out, "PNG")
    print("wrote", out)


if __name__ == "__main__":
    rows: list[tuple[str, bool]] = []
    for host in ("app.velvetelves.com", "api.prod.velvetelves.com"):
        info = tls_handshake(host)
        v12 = tls_handshake(host, only=ssl.TLSVersion.TLSv1_2)
        v10 = try_legacy_tls(host, ssl.TLSVersion.TLSv1)
        v11 = try_legacy_tls(host, ssl.TLSVersion.TLSv1_1)
        tls_ok = info["version"] in ("TLSv1.2", "TLSv1.3")
        v12_ok = v12["version"] == "TLSv1.2"
        legacy_ok = v10 == "rejected" and v11 == "rejected"
        issuer_ok = "amazon" in info["issuer"].lower()
        block = [
            (f"{host}  default TLS {info['version']}  cipher {info['cipher'][:42]}", tls_ok),
            (f"{host}  TLS 1.2 accepted  cipher {v12['cipher'][:42]}", v12_ok),
            (f"{host}  TLS 1.0 {v10}  TLS 1.1 {v11}  (this client)", legacy_ok),
            (f"{host}  cert issuer {info['issuer'][:50]}", issuer_ok),
        ]
        for line, ok in block:
            print(("OK " if ok else "!! "), line)
            rows.append((line, ok))

    spa_https, spa_hsts, _ = https_get("https://app.velvetelves.com/")
    api_https, api_hsts, _ = https_get("https://api.prod.velvetelves.com/api/v1/health")
    spa_http, spa_loc, _, _ = http_get("http://app.velvetelves.com/")
    api_http, api_loc, api_ctype, api_body = http_get("http://api.prod.velvetelves.com/api/v1/health")

    extra = [
        (f"GET https://app.velvetelves.com/  HTTP {spa_https}  HSTS {spa_hsts[:50]}", spa_https == 200 and "max-age" in spa_hsts.lower()),
        (f"GET https://api.prod.velvetelves.com/api/v1/health  HTTP {api_https}  HSTS {api_hsts[:40]}", api_https == 200 and "max-age" in api_hsts.lower()),
        (f"GET http://app.velvetelves.com/  HTTP {spa_http} Location {spa_loc[:48]}", spa_http in (301, 302, 308) and "https://" in spa_loc.lower()),
        (
            f"GET http://api.prod.velvetelves.com/api/v1/health  HTTP {api_http}  {api_ctype[:24]}  (cleartext API)",
            False,
        ),
    ]
    if api_http != 200:
        extra[-1] = (
            f"GET http://api.prod.velvetelves.com/api/v1/health  HTTP {api_http} Location {api_loc[:40]}",
            api_http in (301, 302, 308) and "https://" in api_loc.lower(),
        )
    for line, ok in extra:
        print(("OK " if ok else "!! "), line)
        rows.append((line, ok))
    print("http api body", api_body[:80])
    render(rows)
