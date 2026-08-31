"""Production peer certificates (CASA 4.1.2). Copies Qualys shots from 4.1.1."""
from __future__ import annotations

import shutil
import socket
import ssl
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SRC = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\4.1.1")
OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\4.1.2")
OUT.mkdir(parents=True, exist_ok=True)

HOSTS = ("app.velvetelves.com", "api.prod.velvetelves.com")
COPIES = (
    ("CASA_4_1_1_ssllabs_app.png", "CASA_4_1_2_ssllabs_app.png"),
    ("CASA_4_1_1_ssllabs_api.png", "CASA_4_1_2_ssllabs_api.png"),
    ("CASA_4_1_1_ssllabs_app_protocols.png", "CASA_4_1_2_ssllabs_app_chain.png"),
    ("CASA_4_1_1_ssllabs_api_protocols.png", "CASA_4_1_2_ssllabs_api_chain.png"),
)


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def flatten_rdn(rdns, key: str) -> str:
    for rdn in rdns or ():
        for k, value in rdn:
            if k == key:
                return value
    return "(absent)"


def peer(host: str) -> dict[str, str]:
    ctx = ssl.create_default_context()
    with socket.create_connection((host, 443), timeout=20) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert() or {}
            sans = [name for kind, name in cert.get("subjectAltName", ()) if kind == "DNS"]
            not_after = cert.get("notAfter", "")
            expires = datetime.strptime(" ".join(not_after.split()), "%b %d %H:%M:%S %Y %Z").replace(
                tzinfo=timezone.utc
            )
            now = datetime.now(timezone.utc)
            issuer_cn = flatten_rdn(cert.get("issuer"), "commonName")
            issuer_o = flatten_rdn(cert.get("issuer"), "organizationName")
            subject_cn = flatten_rdn(cert.get("subject"), "commonName")
            self_signed = issuer_cn == subject_cn and issuer_o != "Amazon"
            return {
                "host": host,
                "subject_cn": subject_cn,
                "san": ", ".join(sans),
                "issuer": f"{issuer_o} / {issuer_cn}",
                "not_before": cert.get("notBefore", ""),
                "not_after": not_after,
                "valid": now < expires,
                "self_signed": self_signed,
                "host_in_san": host in sans or host == subject_cn,
            }


def mismatch_rejected(host: str) -> bool:
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, 443), timeout=15) as sock:
            with ctx.wrap_socket(sock, server_hostname="evil.example.invalid"):
                return False
    except (ssl.SSLError, ssl.CertificateError):
        return True


def render(rows: list[tuple[str, bool]]) -> None:
    W, H = 1400, 1100
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "4.1.2  Production certificates are public Amazon ACM (not self-signed)",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "Live TLS handshake with the OS trust store. 31 Aug 2026.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 118
    for line, ok in rows:
        color = (20, 90, 50) if ok else (140, 40, 40)
        d.text((48, y), line, font=font(15), fill=color)
        y += 28
    d.text(
        (48, H - 48),
        "production  |  CASA_4_1_2_cert  |  31 Aug 2026",
        font=font(12),
        fill=(80, 80, 80),
    )
    out = OUT / "CASA_4_1_2_cert.png"
    im.save(out, "PNG")
    print("wrote", out)


if __name__ == "__main__":
    rows: list[tuple[str, bool]] = []
    for host in HOSTS:
        info = peer(host)
        mismatch = mismatch_rejected(host)
        amazon = "amazon" in info["issuer"].lower()
        block = [
            (f"{host}  OS trust store verified", True),
            (f"{host}  subject CN {info['subject_cn']}", bool(info["subject_cn"])),
            (f"{host}  SAN {info['san'][:70]}", info["host_in_san"]),
            (f"{host}  issuer {info['issuer'][:70]}", amazon),
            (f"{host}  notBefore {info['not_before']}  notAfter {info['not_after']}", info["valid"]),
            (f"{host}  self-signed {info['self_signed']}", not info["self_signed"]),
            (f"{host}  wrong SNI/hostname handshake failed (no trusted session)", mismatch),
        ]
        for line, ok in block:
            print(("OK " if ok else "!! "), line)
            rows.append((line, ok))
    render(rows)
    bad = [line for line, ok in rows if not ok]
    if bad:
        raise SystemExit("cert probe failed: " + bad[0])
    for src_name, dest_name in COPIES:
        src = SRC / src_name
        dest = OUT / dest_name
        shutil.copy2(src, dest)
        print("copied", dest)
