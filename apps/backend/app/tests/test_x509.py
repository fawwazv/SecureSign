"""Test P1: sertifikat self-signed (tanpa jaringan, tanpa DB)."""

from __future__ import annotations

from cryptography import x509

from app.crypto import ecdsa, rsa
from app.crypto.x509 import cert_matches_key, issue_self_signed


def test_rsa_cert_subject_dan_match() -> None:
    priv, pub = rsa.generate()
    cert_pem = issue_self_signed(priv, "Sinta Prabowo", "sinta@pt.id")
    assert "BEGIN CERTIFICATE" in cert_pem
    cert = x509.load_pem_x509_certificate(cert_pem.encode())
    cn = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value
    assert cn == "Sinta Prabowo"
    assert cert.issuer == cert.subject  # self-signed
    assert cert_matches_key(cert_pem, pub) is True


def test_ecdsa_cert_match() -> None:
    priv, pub = ecdsa.generate()
    cert_pem = issue_self_signed(priv, "Budi", "budi@pt.id")
    assert cert_matches_key(cert_pem, pub) is True


def test_ed25519_ditolak() -> None:
    from app.crypto import ed25519

    priv, _ = ed25519.generate()
    try:
        issue_self_signed(priv, "X", "x@pt.id")
        raise AssertionError("harus ditolak")
    except TypeError:
        pass


def test_cert_salah_tidak_match() -> None:
    priv, _ = rsa.generate()
    _, pub2 = rsa.generate()
    cert_pem = issue_self_signed(priv, "A", "a@pt.id")
    assert cert_matches_key(cert_pem, pub2) is False
