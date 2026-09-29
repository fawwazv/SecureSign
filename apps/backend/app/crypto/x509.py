"""Sertifikat X.509 self-signed untuk PAdES demo.

Bukan pengganti sertifikat PSrE tersertifikasi — hanya agar PDF bertanda
dapat divalidasi strukturnya (termasuk Adobe Reader, sebagai "tidak tepercaya").
Hanya untuk kunci RSA/ECDSA; Ed25519 tetap jalur detached legacy.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import NameOID

VALIDITY_DAYS = 5 * 365


def issue_self_signed(private_pem: bytes, common_name: str, email: str) -> str:
    """Terbitkan sertifikat self-signed dari private key PEM. Return PEM string."""
    key = serialization.load_pem_private_key(private_pem, password=None)
    if not isinstance(key, (rsa.RSAPrivateKey, ec.EllipticCurvePrivateKey)):
        raise TypeError("Sertifikat PAdES hanya untuk RSA/ECDSA.")
    name = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, (common_name or email)[:64]),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, email),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SignVault Demo"),
        ]
    )
    now = datetime.now(UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=VALIDITY_DAYS))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=True,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(private_key=key, algorithm=hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")


def cert_matches_key(cert_pem: str, public_pem: bytes) -> bool:
    """Pastikan sertifikat mengikat public key yang benar."""
    cert = x509.load_pem_x509_certificate(cert_pem.encode())
    pub = serialization.load_pem_public_key(public_pem)
    a = cert.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    b = pub.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return a == b
