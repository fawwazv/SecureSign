"""ECDSA P-256 (SHA-256) — prd.md §8."""

from __future__ import annotations

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


def generate() -> tuple[bytes, bytes]:
    key = ec.generate_private_key(ec.SECP256R1())
    return _priv_bytes(key), _pub_bytes(key)


def sign(private_pem: bytes, message: bytes) -> bytes:
    key = serialization.load_pem_private_key(private_pem, password=None)
    assert isinstance(key, ec.EllipticCurvePrivateKey)
    return key.sign(message, ec.ECDSA(hashes.SHA256()))


def verify(public_pem: bytes, message: bytes, signature: bytes) -> bool:
    key = serialization.load_pem_public_key(public_pem)
    assert isinstance(key, ec.EllipticCurvePublicKey)
    try:
        key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False


def _priv_bytes(key: ec.EllipticCurvePrivateKey) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def _pub_bytes(key: ec.EllipticCurvePrivateKey) -> bytes:
    return key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
