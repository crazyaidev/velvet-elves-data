"""Local Fernet round-trip for CASA 4.1.3. Uses an ephemeral key — never production ENCRYPTION_KEY."""
from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images\4.1.3")
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    p = Path(rf"C:\Windows\Fonts\{name}")
    if p.exists():
        return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def main() -> None:
    f = Fernet(Fernet.generate_key())
    sample = b"sample-not-production"
    token = f.encrypt(sample)
    prefix = token[:8].decode("ascii", errors="replace")
    roundtrip = f.decrypt(token) == sample
    plaintext_in_ct = sample.decode() in token.decode("ascii", errors="replace")
    tampered = bytearray(token)
    tampered[-2] ^= 0x01
    try:
        f.decrypt(bytes(tampered))
        tamper = "accepted (unexpected)"
        tamper_ok = False
    except InvalidToken:
        tamper = "InvalidToken"
        tamper_ok = True

    rows = [
        (f"Fernet.encrypt sample  prefix {prefix}  len {len(token)}", True),
        (f"plaintext appears in ciphertext  {plaintext_in_ct}", not plaintext_in_ct),
        (f"decrypt round-trip  {roundtrip}", roundtrip),
        (f"tampered token  {tamper}", tamper_ok),
        ("key  ephemeral (not ENCRYPTION_KEY, not printed)", True),
        ("algorithm  AES-128-CBC + HMAC-SHA256  (cryptography Fernet)", True),
    ]

    W, H = 1400, 720
    im = Image.new("RGB", (W, H), (248, 248, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10), fill=(200, 80, 70))
    d.text(
        (48, 32),
        "4.1.3  Fernet round-trip (ephemeral key, not production)",
        font=font(22, True),
        fill=(24, 24, 24),
    )
    d.text(
        (48, 68),
        "Same library as app/utils/encryption.py. Ciphertext body not shown.",
        font=font(14),
        fill=(80, 80, 80),
    )
    y = 120
    for line, ok in rows:
        color = (20, 90, 50) if ok else (140, 40, 40)
        d.text((48, y), line, font=font(16), fill=color)
        y += 32
    d.text((48, H - 48), "CASA_4_1_3_fernet  |  31 Aug 2026", font=font(12), fill=(80, 80, 80))
    out = OUT / "CASA_4_1_3_fernet.png"
    im.save(out, "PNG")
    print("wrote", out)
    print("prefix", prefix, "len", len(token), "roundtrip", roundtrip, "tamper", tamper)


if __name__ == "__main__":
    main()
