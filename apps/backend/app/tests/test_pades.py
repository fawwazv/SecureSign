"""Test P2: PAdES RSA-PSS via pyHanko (roundtrip, ByteRange, tamper)."""

from __future__ import annotations

import asyncio
import io

import pytest
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature

from app.crypto import rsa
from app.crypto.key_manager import decrypt_private, encrypt_private
from app.crypto.x509 import issue_self_signed
from app.services.pades import (
    appearance_box_for,
    fraction_to_box,
    read_byte_range,
    sign_pdf_pades,
    validate_pades,
)


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _pdf() -> bytes:
    import io as _io

    from reportlab.pdfgen import canvas

    buf = _io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(595, 842))
    c.drawString(72, 800, "PAdES test")
    c.save()
    return buf.getvalue()


@pytest.fixture()
def keycert():
    priv, _ = rsa.generate()
    enc, nonce = encrypt_private(priv)
    cert = issue_self_signed(decrypt_private(enc, nonce), "Tester", "t@tes.id")
    return decrypt_private(enc, nonce), cert


def test_pades_roundtrip_valid(keycert) -> None:
    priv, cert = keycert
    signed, br, cms = _run(
        sign_pdf_pades(
            _pdf(),
            private_pem=priv,
            cert_pem=cert,
            box_frac=(1, 0.6, 0.7, 0.15),
            appearance_lines=["Ditandatangani: Tester", "ID: sv_x"],
        )
    )
    assert br and len(br.split()) == 4  # ByteRange tercatat
    assert cms  # CMS base64 tersimpan
    assert read_byte_range(signed) == br
    sigs = list(PdfFileReader(io.BytesIO(signed)).embedded_signatures)
    assert len(sigs) == 1
    status = validate_pdf_signature(sigs[0])
    assert status.valid is True and status.intact is True
    # PSS dibuktikan di level CMS.
    from asn1crypto import cms as asn1_cms

    algos = {
        str(a["algorithm"]) for a in [sigs[0].signed_data["signer_infos"][0]["signature_algorithm"]]
    }
    assert "1.2.840.113549.1.1.10" in algos  # RSASSA-PSS
    _ = asn1_cms


def test_pades_tamper_byte_gagal(keycert) -> None:
    priv, cert = keycert
    signed, _, _ = _run(
        sign_pdf_pades(
            _pdf(),
            private_pem=priv,
            cert_pem=cert,
            box_frac=None,
            appearance_lines=["Tester"],
        )
    )
    bad = bytearray(signed)
    bad[100] ^= 0x01  # ubah 1 byte di area bertanda
    sigs = list(PdfFileReader(io.BytesIO(bytes(bad))).embedded_signatures)
    assert len(sigs) == 1
    status = validate_pdf_signature(sigs[0])
    # intact=False berarti isi bertanda berubah -> tolak.
    assert not (status.valid is True and status.intact is True)


def test_fraction_to_box() -> None:
    pdf = _pdf()
    (x0, y0, x1, y1), idx = fraction_to_box(pdf, 1, 0.5, 0.5, 0.1)
    assert idx == 0 and 0 <= x0 < x1 <= 595 and 0 <= y0 < y1 <= 842


def test_appearance_box_di_bawah_dan_clamp() -> None:
    pdf = _pdf()
    # QR di tengah -> teks tepat di bawahnya, dalam halaman.
    (x0, y0, x1, y1), _ = appearance_box_for(pdf, (1, 0.5, 0.3, 0.1))
    assert 0 <= x0 < x1 <= 595 and 0 <= y0 < y1 <= 842
    assert y1 - y0 <= 44.0 + 1
    # QR mepet bawah -> teks pindah ke atas QR, tetap dalam halaman.
    (a0, b0, a1, b1), _ = appearance_box_for(pdf, (1, 0.5, 0.98, 0.1))
    assert 0 <= a0 < a1 <= 595 and 0 <= b0 < b1 <= 842


def _pub_pem(priv: bytes) -> str:
    from cryptography.hazmat.primitives import serialization

    key = serialization.load_pem_private_key(priv, password=None)
    return (
        key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )


def test_validate_ok_dan_wrong_key_dan_tamper(keycert) -> None:
    priv, cert = keycert
    pub_pem = _pub_pem(priv)
    signed, _, _ = _run(
        sign_pdf_pades(
            _pdf(), private_pem=priv, cert_pem=cert, box_frac=None, appearance_lines=["T"]
        )
    )
    ok = validate_pades(signed, pub_pem)
    assert ok["ok"] is True

    _, pub_other = rsa.generate()
    wrong = validate_pades(signed, pub_other.decode())
    assert wrong["ok"] is False and "cocok" in wrong["reason"]

    bad = bytearray(signed)
    bad[200] ^= 0x01
    tampered = validate_pades(bytes(bad), pub_pem)
    assert tampered["ok"] is False
