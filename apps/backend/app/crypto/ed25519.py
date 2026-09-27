"""Ed25519 (signature 64 byte, public key 32 byte) — prd.md §8."""

from __future__ import annotations

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


def generate() -> tuple[bytes, bytes]:
    key = ed25519.Ed25519PrivateKey.generate()
    return _priv_bytes(key), _pub_bytes(key)


def sign(private_pem: bytes, message: bytes) -> bytes:
    key = serialization.load_pem_private_key(private_pem, password=None)
    assert isinstance(key, ed25519.Ed25519PrivateKey)
    return key.sign(message)


def verify(public_pem: bytes, message: bytes, signature: bytes) -> bool:
    key = serialization.load_pem_public_key(public_pem)
    assert isinstance(key, ed25519.Ed25519PublicKey)
    try:
        key.verify(signature, message)
        return True
    except InvalidSignature:
        return False


def raw_public_key(public_pem: bytes) -> bytes:
    """Public key mentah 32 byte (untuk assert testing prd-backend §7)."""
    key = serialization.load_pem_public_key(public_pem)
    assert isinstance(key, ed25519.Ed25519PublicKey)
    return key.public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )


def _priv_bytes(key: ed25519.Ed25519PrivateKey) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def _pub_bytes(key: ed25519.Ed25519PrivateKey) -> bytes:
    return key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
